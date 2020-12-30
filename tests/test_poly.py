import pytest

from polybench.poly import Polynomial


def test_poly_basic() -> None:
    zero = Polynomial()
    one = Polynomial(1)
    minus_one = Polynomial(-1)

    a = Polynomial("1+x")
    b = Polynomial("1-x")

    assert not zero
    assert one
    assert minus_one
    assert a
    assert b

    assert zero == 0
    assert one == 1
    assert minus_one == -1
    assert a != b

    assert a == Polynomial(a)

    assert str(a) == "1+x" or str(a) == "x+1"

    with pytest.raises(ValueError, match="unexpected expr"):
        Polynomial(1.0)  # type: ignore


def test_poly_as_commutative_ring() -> None:
    zero = Polynomial()
    one = Polynomial(1)

    a = Polynomial("1+x")
    b = Polynomial("1-y")
    c = Polynomial("1+z")

    assert a + b == Polynomial("2+x-y")
    assert a + (b + c) == (a + b) + c
    assert a + b == b + a
    assert a + zero == a
    assert a + (-a) == zero

    assert a * b == Polynomial("1+x-y-x*y")
    assert a * (b * c) == (a * b) * c
    assert a * b == b * a
    assert a * one == a

    assert a * (b + c) == (a * b) + (a * c)
    assert (a + b) * c == (a * c) + (b * c)

    # extra tests

    assert a == +a

    assert a - b == Polynomial("x+y")

    assert a.equals_without_unit(a)
    assert a.equals_without_unit(-a)
