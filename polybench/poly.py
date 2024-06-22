"""Capsulize polynomial operations."""

from typing import Union

import symengine


class Polynomial:
    """Polynomial wrapper class."""

    __slots__ = ("_raw",)

    def __init__(self, expr: Union[str, int, "Polynomial"] = 0) -> None:
        """Construct a polynomial."""
        if isinstance(expr, str):
            p = symengine.sympify(expr)
            self._raw = symengine.expand(p)
        elif isinstance(expr, int):
            self._raw = symengine.sympify(expr)
        elif isinstance(expr, Polynomial):
            self._raw = expr._raw
        else:
            raise ValueError(f"unexpected expr: {expr}")

    def __str__(self) -> str:
        """Return the string representation."""
        return str(self._raw).replace(" ", "").replace("**", "^")

    def __bool__(self) -> bool:
        """Return ``bool(self)``."""
        return not self._raw.is_zero

    def __len__(self) -> int:
        """Return the number of terms in the polynomial."""
        raw = self._raw
        if raw.is_Add:
            return len(raw.args)
        elif raw.is_zero:
            return 0
        else:
            return 1

    def __eq__(self, other: object) -> bool:
        """Return ``self == other``."""
        if isinstance(other, Polynomial):
            return self._raw == other._raw  # type: ignore
        if isinstance(other, int):
            return self._raw == other  # type: ignore
        return NotImplemented

    def __pos__(self) -> "Polynomial":
        """Return ``+ self``."""
        return self

    def __neg__(self) -> "Polynomial":
        """Return ``- self``."""
        result = super().__new__(Polynomial)
        result._raw = symengine.expand(-self._raw)
        return result

    def __add__(self, other: "Polynomial") -> "Polynomial":
        """Return ``self + other``."""
        result = super().__new__(Polynomial)
        result._raw = symengine.expand(self._raw + other._raw)
        return result

    def __sub__(self, other: "Polynomial") -> "Polynomial":
        """Return ``self - other``."""
        result = super().__new__(Polynomial)
        result._raw = symengine.expand(self._raw - other._raw)
        return result

    def __mul__(self, other: "Polynomial") -> "Polynomial":
        """Return ``self * other``."""
        result = super().__new__(Polynomial)
        result._raw = symengine.expand(self._raw * other._raw)
        return result

    def equals_without_unit(self, other: "Polynomial") -> bool:
        """Return `True` if ``self == other`` up to a unit."""
        return self == other or self == -other

    @property
    def is_unit(self) -> bool:
        """True if the polynomial is 1 or -1."""
        return len(self) == 1 and (self == 1 or self == -1)
