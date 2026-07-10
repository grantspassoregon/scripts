from __future__ import annotations
import re
import uuid
from dataclasses import dataclass
from typing import overload, Union, NoReturn

_GUID_CANON_RE = re.compile(
    r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
)


class GuidError(ValueError): ...


@dataclass(frozen=True, slots=True)
class Guid:
    _value: str

    @staticmethod
    def _normalize(s: str) -> str:
        s = s.strip().upper()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1]
        if len(s) == 32 and "-" not in s:
            s = f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"
        return s

    @classmethod
    def parse(cls, any_str: str) -> Guid:
        s = cls._normalize(any_str)
        if not _GUID_CANON_RE.match(s):
            raise GuidError(f"Invalid GUID format: {any_str!r}")
        uuid.UUID(s)  # deep validation
        return cls(s)

    BytesLike = Union[bytes, bytearray, memoryview]

    @overload
    @classmethod
    def from_db(cls, db_value: str) -> Guid: ...
    @overload
    @classmethod
    def from_db(cls, db_value: uuid.UUID) -> Guid: ...
    @overload
    @classmethod
    def from_db(cls, db_value: BytesLike) -> Guid: ...
    @overload
    @classmethod
    def from_db(cls, db_value: None) -> NoReturn: ...

    @classmethod
    def from_db(cls, db_value) -> Guid:
        # Explicitly reject None here (reachable, type-checked).
        if db_value is None:
            raise GuidError("GUID cannot be None.")

        if isinstance(db_value, uuid.UUID):
            return cls(str(db_value).upper())
        if isinstance(db_value, str):
            return cls.parse(db_value)
        if isinstance(db_value, (bytes, bytearray, memoryview)):
            s = bytes(db_value).decode("ascii", errors="ignore")
            return cls.parse(s)
        raise GuidError(f"Unsupported DB value type: {type(db_value).__name__}")

    def __str__(self) -> str:
        return self._value

    def to_uuid(self) -> uuid.UUID:
        return uuid.UUID(self._value)

    def with_braces(self) -> str:
        return "{" + self._value + "}"

    def sql_literal(self) -> str:
        return f"'{self._value}'"
