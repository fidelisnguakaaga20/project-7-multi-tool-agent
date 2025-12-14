import pytest
from app.tools.calculator import calculator_tool

def test_basic_math():
    assert calculator_tool({"expression": "19*23"})["result"] == 437

def test_parentheses():
    assert calculator_tool({"expression": "(10+2)*3"})["result"] == 36

def test_reject_invalid_chars():
    with pytest.raises(ValueError):
        calculator_tool({"expression": "2+2; import os"})
