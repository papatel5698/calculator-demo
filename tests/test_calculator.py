import pytest
from src.calculator import add, subtract, multiply, divide, evaluate, parse_expression


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_multiply():
    assert multiply(3, 4) == 12


def test_divide_integer():
    assert divide(7, 2) == 3.5


def test_divide_decimal_result():
    assert divide(10, 3) == pytest.approx(3.333333, rel=1e-4)


def test_divide_exact():
    assert divide(10, 2) == 5.0


def test_evaluate_division():
    assert evaluate("7/2") == 3.5


def test_divide_by_zero():
    # This will crash because there is no ZeroDivisionError handling
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


def test_evaluate_simple_add():
    assert evaluate("2+3") == 5


def test_evaluate_simple_multiply():
    assert evaluate("3*4") == 12


def test_operator_precedence():
    # This will fail because calculator evaluates left-to-right
    assert evaluate("2+3*4") == 14


def test_evaluate_with_spaces():
    # This will fail because parser doesn't handle spaces
    assert evaluate("2 + 3") == 5


def test_empty_input():
    # This will crash because no empty input handling
    with pytest.raises(Exception):
        evaluate("")


def test_negative_number():
    # This will fail because parser can't handle leading minus
    assert evaluate("-5+3") == -2
