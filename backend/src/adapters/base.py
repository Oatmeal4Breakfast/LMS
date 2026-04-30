from abc import ABC, abstractmethod
from uuid import UUID


class AbstractRepository[T](ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add(self, entity: T) -> None:
        raise NotImplementedError
