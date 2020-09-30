from abc import ABC, abstractmethod
from uuid import UUID


class Game(ABC):
    @property
    @abstractmethod
    def owner(self) -> UUID:
        raise NotImplementedError()

    @property
    @abstractmethod
    def room(self) -> UUID:
        raise NotImplementedError()

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def uuid(self) -> UUID:
        raise NotImplementedError()