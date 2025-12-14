import ast
import operator as op
import re

# Stage 3: safe calculator (no eval)
_ALLOWED = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def _sanitize(expr: str) -> str:
    expr = expr.strip()
    # allow only digits, operators, parentheses, decimal dots, spaces
    if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s]+", expr):
        raise ValueError("Expression contains invalid characters.")
    return expr

def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED:
        return _ALLOWED[type(node.op)](_eval(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED:
        left = _eval(node.left)
        right = _eval(node.right)
        return _ALLOWED[type(node.op)](left, right)

    raise ValueError("Unsupported expression.")

def calculator_tool(inp: dict) -> dict:
    expr = inp.get("expression", "")
    expr = _sanitize(expr)

    tree = ast.parse(expr, mode="eval")
    result = _eval(tree)

    # Normalize floats like 1.0 -> 1
    if isinstance(result, float) and result.is_integer():
        result = int(result)

    return {"result": result}
