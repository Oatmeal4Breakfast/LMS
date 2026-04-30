# Bidirectional Relationship Conversion Problem

## Context

In `avit-training`, the domain is organized around `TrainingPath → Lesson → Quiz → Question`
with `User` entities assigned to training paths. The problem arises because `User` and
`TrainingPath` hold **full object references to each other** across two layers — the domain
entities (`entities.py`) and the ORM models (`schemas.py`).

---

## The Problem in Detail

### Current entity definitions

```python
# entities.py

@dataclass
class TrainingPath:
    title: str
    department: Department
    lessons: list[Lesson] = field(default_factory=list)
    assigned_users: list[User] = field(default_factory=list)  # ← back-ref to User
    id: UUID = field(default_factory=uuid7)

@dataclass
class User:
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    department: Department
    training_paths: list[TrainingPath] = field(default_factory=list)  # ← back-ref to TrainingPath
    ...
```

### Current ORM model definitions

```python
# schemas.py

class TrainingPathModel(Base):
    __tablename__ = "training_path"
    assigned_users: Mapped[list["UserModel"]] = relationship(
        back_populates="training_paths"
    )
    ...

class UserModel(Base):
    __tablename__ = "user_account"
    training_paths: Mapped[list["TrainingPathModel"]] = relationship(
        "TrainingPath", secondary="user_training_path", back_populates="assigned_users"
    )
    ...
```

### Where conversion happens

`UserRepository` has `_to_entity` and `_to_model` methods that translate between the two
layers. The problem surfaces in both directions:

**`_to_entity` (ORM → domain):**
```python
def _to_entity(self, user_model: UserModel) -> User:
    return User(
        ...
        training_paths=user_model.training_paths,  # ❌ list[TrainingPathModel], not list[TrainingPath]
    )
```

To fix this, you'd need to convert each `TrainingPathModel → TrainingPath`. But
`TrainingPath.assigned_users` is `list[User]`, so you'd then need to convert each
`UserModel → User` again — which loops back and causes **infinite recursion**.

**`_to_model` (domain → ORM):**
```python
def _to_model(self, user: User) -> UserModel:
    return UserModel(
        ...
        training_paths=user.training_paths,  # ❌ list[TrainingPath], not list[TrainingPathModel]
    )
```

SQLAlchemy's relationship expects `list[TrainingPathModel]` instances that are already
tracked by the session — not freshly constructed domain entity objects.

**`update`:**
```python
model.training_paths = entity.training_paths  # ❌ same type mismatch
```

---

## Why This Happens

This is a classic **aggregate boundary violation**. `User` and `TrainingPath` are two
separate aggregates — independently meaningful, independently persisted. Holding full
object references across aggregate boundaries in both directions creates:

1. A **circular object graph** that is impossible to fully serialize or convert without
   choosing an arbitrary stopping point.
2. **Tight coupling** between aggregates — a change to `User` requires knowing about
   `TrainingPath` and vice versa.
3. **Unclear ownership** — if you update `user.training_paths[0].title`, does that
   update the `TrainingPath` aggregate? Through which repository?

---

## The Options

---

### Option 1: Break the cycle — don't populate back-references

When converting `TrainingPathModel → TrainingPath` inside `UserRepository`, set
`assigned_users=[]`. Accept that some fields will be unpopulated depending on which
repository fetched the data.

```python
# UserRepository

def _to_entity(self, user_model: UserModel) -> User:
    return User(
        ...
        training_paths=[self._tp_to_entity(tp) for tp in user_model.training_paths],
    )

@staticmethod
def _tp_to_entity(model: TrainingPathModel) -> TrainingPath:
    return TrainingPath(
        id=model.id,
        title=model.title,
        department=model.department,
        lessons=[],         # not loaded here
        assigned_users=[],  # ← break the cycle explicitly
    )
```

**Pros:**
- Minimal change — no new files or abstractions
- Fixes the immediate type error and infinite recursion

**Cons:**
- `TrainingPath` entities returned via `UserRepository` will always have empty
  `assigned_users`. There is no way for callers to tell if `[]` means "no users assigned"
  or "not loaded". This is a **hidden data completeness problem**.
- Duplicates conversion logic if a `TrainingPathRepository` is later introduced.
- Still doesn't solve `_to_model` — you can't pass `list[TrainingPath]` to a SQLAlchemy
  relationship that expects session-tracked `list[TrainingPathModel]` instances.

---

### Option 2: Flatten cross-references to UUIDs ✅ Recommended

Change the entity model so that references **across aggregate boundaries** are represented
as IDs, not full objects. Each aggregate only owns its children — it references other
aggregates by ID only.

```python
# entities.py — after

@dataclass
class TrainingPath:
    title: str
    department: Department
    lessons: list[Lesson] = field(default_factory=list)   # owned — keep as objects
    assigned_user_ids: list[UUID] = field(default_factory=list)  # reference — use IDs
    id: UUID = field(default_factory=uuid7)

@dataclass
class User:
    email: str
    ...
    training_path_ids: list[UUID] = field(default_factory=list)  # reference — use IDs
    completed_lessons: list[UUID] = field(default_factory=list)
    ...
```

The ORM models and repository conversions become trivial:

```python
# schemas.py — UserModel still has the relationship for DB queries,
# but the entity just holds IDs extracted from it

def _to_entity(self, user_model: UserModel) -> User:
    return User(
        ...
        training_path_ids=[tp.id for tp in user_model.training_paths],  # ✅ just extract IDs
    )

def _to_model(self, user: User) -> UserModel:
    return UserModel(
        ...
        # training_paths relationship managed separately — don't set in constructor
    )
```

To assign a user to a training path, you'd load both from their respective repositories
and update the relationship explicitly:

```python
# In a service
async def assign_training_path(self, user_id: UUID, training_path_id: UUID):
    user_model = await self.session.get(UserModel, user_id)
    tp_model = await self.session.get(TrainingPathModel, training_path_id)
    user_model.training_paths.append(tp_model)   # SQLAlchemy manages the join table
```

**Pros:**
- **Eliminates the cycle entirely** — `_to_entity` and `_to_model` become straightforward
- Aligns with DDD aggregate design — aggregates reference each other by ID, never by object
- Matches how the database actually works (the secondary join table stores UUID pairs)
- Entities are lighter and easier to serialize/test

**Cons:**
- Callers assembling the full graph (e.g., "get user with their training path titles")
  need two queries — one for the user, one for the training paths by ID
- Requires updating `entities.py` and any code that currently accesses
  `user.training_paths[0].title` etc.

---

### Option 3: Separate read models per query

Keep entities lean (using Option 2's flat IDs), and introduce purpose-built Pydantic
response models in `api.py` that assemble the full picture for specific endpoints.

```python
# api.py

class TrainingPathSummary(BaseModel):
    id: UUID
    title: str
    department: Department

class UserWithPathsResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    training_paths: list[TrainingPathSummary]  # assembled in the router/service

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    training_path_ids: list[UUID]  # flat — for endpoints that don't need full path data
```

In the service or router:

```python
async def get_user_with_paths(user_id: UUID, db: AsyncSession) -> UserWithPathsResponse:
    user = await user_repo.get_by_id(user_id)              # User entity (flat IDs)
    paths = await tp_repo.get_by_ids(user.training_path_ids)  # list[TrainingPath]
    return UserWithPathsResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        training_paths=[TrainingPathSummary(id=tp.id, title=tp.title, department=tp.department) for tp in paths],
    )
```

**Pros:**
- Each endpoint gets exactly the data shape it needs — no over-fetching
- API contracts are explicit and versioned independently of domain entities
- Entities stay clean; response models handle presentation concerns

**Cons:**
- More types to define and maintain
- Service/router layer does more assembly work
- Easy to let response models grow bloated over time without discipline

---

### Option 4: Lazy load — explicit fetch methods on the repository

Never convert relationships in the base `_to_entity`. Add dedicated methods when the
full graph is actually needed.

```python
class UserRepository(AbstractRepository[User]):

    async def get_by_id(self, id: UUID) -> Optional[User]:
        # Returns User with training_path_ids only (flat)
        ...

    async def get_with_training_paths(self, id: UUID) -> Optional[tuple[User, list[TrainingPath]]]:
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.training_paths))
            .where(UserModel.id == id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        user = self._to_entity(model)
        paths = [self._tp_to_entity(tp) for tp in model.training_paths]
        return user, paths
```

**Pros:**
- Very explicit — callers always know exactly what's loaded
- Base conversion stays simple
- The `selectinload` / `joinedload` hint tells SQLAlchemy to eagerly load the
  relationship in one query, avoiding the N+1 problem

**Cons:**
- Proliferation of `get_with_X` methods as the app grows
- Callers receive a tuple or a special object — slightly awkward to work with
- Still doesn't resolve the entity-level circular reference in `entities.py`

---

## Recommendation

**Option 2 as the foundation + Option 3 for the API layer.**

1. **Fix `entities.py`**: Replace `list[TrainingPath]` on `User` with `list[UUID]`
   (rename to `training_path_ids`). Remove `assigned_users: list[User]` from
   `TrainingPath` (or replace with `assigned_user_ids: list[UUID]`).

2. **Fix `_to_entity` / `_to_model`**: Conversion is now trivial — extract IDs from
   the SQLAlchemy relationship on read, leave relationship management to explicit
   service-layer operations on write.

3. **Build response models in `api.py`**: When an endpoint needs the full user +
   training path data, assemble it in the service layer from two repository calls and
   return a purpose-built Pydantic response model.

This design keeps each layer doing one job cleanly:
- `entities.py` — pure domain logic, no ORM or HTTP concerns
- `schemas.py` — persistence shape, SQLAlchemy manages relationships
- `repository.py` — translate between the two, keep conversions simple
- `api.py` — compose data for HTTP responses
- `services/` — orchestrate multi-repository operations

---

## Quick Reference: What Changes

| File | Change |
|---|---|
| `entities.py` | `User.training_paths: list[TrainingPath]` → `training_path_ids: list[UUID]` |
| `entities.py` | `TrainingPath.assigned_users: list[User]` → remove or → `assigned_user_ids: list[UUID]` |
| `repository.py` | `_to_entity`: `training_path_ids=[tp.id for tp in model.training_paths]` |
| `repository.py` | `_to_model`: omit `training_paths` from constructor; manage via session in service |
| `repository.py` | `update`: replace `model.training_paths = entity.training_paths` with explicit session load |
| `api.py` | Add `UserWithPathsResponse` and `TrainingPathSummary` for endpoints that need the full graph |
| `services/` | Add `assign_training_path(user_id, tp_id)` to manage the many-to-many relationship |
