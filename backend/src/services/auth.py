import jwt

from datetime import timedelta, datetime, UTC

from src.domain.user import User
from src.adapters.unit_of_work import UnitOfWork
from src.core.security import hasher, verify_password_hash
from src.core.logging import get_logger
from src.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    UserNotFoundError,
    DatabaseUnavailableError,
    ServiceUnavailableError,
)


logger = get_logger(__name__)


class AuthService:
    def __init__(self, uow: UnitOfWork, jwt_secret: str, algorithm: str) -> None:
        self._uow: UnitOfWork = uow
        self._jwt_secret: str = jwt_secret
        self._algorithm: str = algorithm
        self._hasher = hasher

    async def get_user_by_email(self, email: str) -> User:
        logger.debug(event="fetching user by email", email=email)

        async with self._uow as uow:
            try:
                user: User | None = await uow.user.get_by_email(email=email)
                if user is None:
                    logger.error(event="UserNotFoundError", email=email)
                    raise UserNotFoundError(f"User with email {email} not found")
                logger.info(event="User retrieved by email", email=email)
                return user
            except DatabaseUnavailableError as e:
                logger.error(event="ServiceUnavailableError", err=str(e))
                raise ServiceUnavailableError from e

    async def authenticate_user(self, email: str, password: str) -> User:
        stored_user: User = await self.get_user_by_email(email=email)
        if not verify_password_hash(
            plain_password=password, hashed_password=str(stored_user.hashed_password)
        ):
            logger.error(event="AuthenticationError", email=email)
            raise AuthenticationError(email)
        return stored_user

    async def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        to_encode: dict = data.copy()
        if expires_delta:
            expire: datetime = datetime.now(UTC) + expires_delta
        else:
            expire: datetime = datetime.now(UTC) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(
            payload=to_encode, key=self._jwt_secret, algorithm=self._algorithm
        )

    async def verify_access_token(self, token: str) -> User | None:
        email: str | None = None
        try:
            payload: dict[str, str | list] = jwt.decode(
                jwt=token, key=self._jwt_secret, algorithms=[self._algorithm]
            )
            email: str | None = payload.get("sub")
            if email is None:
                return None
            return await self.get_user_by_email(email=email)
        except jwt.PyJWTError:
            logger.error(event="InvalidTokenError", email=email, token=token)
            raise InvalidTokenError(f"Unable to decode JWT Token {token}")
