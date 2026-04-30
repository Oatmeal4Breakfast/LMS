from enum import StrEnum, auto


class UserType(StrEnum):
    ADMIN = auto()
    STAFF = auto()
    TRAINER = auto()


class Department(StrEnum):
    POS = auto()
    IT = auto()
    AV = auto()


class ContentStatus(StrEnum):
    DRAFT = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()
