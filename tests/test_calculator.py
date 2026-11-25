import pytest

from src.calculator import add, subtract, multiply, divide, evaluate, parse_expression


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_multiply():
    assert multiply(3, 4) == 12


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Intentional demo bug: divide() uses // instead of /. A fix must remove this marker.")
def test_divide_integer():
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    # This will crash because there is no ZeroDivisionError handling
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


def test_evaluate_simple_add():
    assert evaluate("2+3") == 5


def test_evaluate_simple_multiply():
    assert evaluate("3*4") == 12


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Intentional demo bug: evaluate() ignores operator precedence. A fix must remove this marker.")
def test_operator_precedence():
    assert evaluate("2+3*4") == 14


@pytest.mark.xfail(strict=True, raises=ValueError, reason="Intentional demo bug: the parser rejects spaces. A fix must remove this marker.")
def test_evaluate_with_spaces():
    assert evaluate("2 + 3") == 5


def test_empty_input():
    # This will crash because no empty input handling
    with pytest.raises(Exception):
        evaluate("")


@pytest.mark.xfail(strict=True, raises=ValueError, reason="Intentional demo bug: the parser can't read a leading minus. A fix must remove this marker.")
def test_negative_number():
    assert evaluate("-5+3") == -2


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Intentional demo bug: operations write to the module-level `result`. A fix must remove this marker.")
def test_evaluate_leaves_no_module_state():
    import src.calculator as calculator
    calculator.result = 0
    evaluate("2+3")
    assert calculator.result == 0
