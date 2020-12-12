"""
A small, safe expression evaluator.

eval() is dangerous on user input, so instead the expression is parsed
with the ast module and only numbers, basic operators and a whitelist
of math functions are allowed.
"""
import ast
import math
import operator

MAX_POWER = 1000
MAX_FACTORIAL = 500

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _factorial(n):
    if n != int(n) or n < 0:
        raise ValueError("factorial only works on whole numbers 0 or above")
    if n > MAX_FACTORIAL:
        raise ValueError(f"factorial is limited to {MAX_FACTORIAL}")
    return math.factorial(int(n))


def _log(x, base=10):
    return math.log(x, base)


def make_functions(degrees=True):
    """Trig functions use degrees by default since that's what most people expect."""
    if degrees:
        to_rad = math.radians
        from_rad = math.degrees
    else:
        to_rad = from_rad = lambda x: x

    return {
        "sin": lambda x: math.sin(to_rad(x)),
        "cos": lambda x: math.cos(to_rad(x)),
        "tan": lambda x: math.tan(to_rad(x)),
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "sqrt": math.sqrt,
        "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
        "log": _log,
        "ln": math.log,
        "log2": math.log2,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "fact": _factorial,
        "factorial": _factorial,
        "rad": math.radians,
        "deg": math.degrees,
    }


class CalcError(Exception):
    pass


def _clean(expression):
    expr = expression.strip().strip("`")
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/")
    expr = expr.replace("π", "pi")
    # allow "5!" style factorial for single numbers
    if expr.endswith("!") and expr[:-1].strip().isdigit():
        expr = f"fact({expr[:-1].strip()})"
    return expr


def evaluate(expression, degrees=True):
    expr = _clean(expression)
    if not expr:
        raise CalcError("Give me something to calculate.")
    if len(expr) > 200:
        raise CalcError("That expression is too long.")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise CalcError("I couldn't understand that expression.")

    functions = make_functions(degrees)

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        # numbers (Python 3.8 uses ast.Constant, older versions ast.Num)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.Name):
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise CalcError(f"Unknown name `{node.id}`")

        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER:
                raise CalcError("That power is too big for me.")
            return OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](_eval(node.operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in functions:
                raise CalcError(f"Unknown function `{name}`")
            args = [_eval(a) for a in node.args]
            return functions[name](*args)

        raise CalcError("That expression has something I can't calculate.")

    try:
        result = _eval(tree)
    except CalcError:
        raise
    except ZeroDivisionError:
        raise CalcError("You can't divide by zero!")
    except (ValueError, TypeError) as e:
        raise CalcError(f"Math error: {e}")
    except OverflowError:
        raise CalcError("The result is too large.")

    return result


def format_number(value):
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        # get rid of floating point noise like 0.30000000000000004
        return f"{value:.10g}"
    text = str(value)
    if len(text) > 300:
        return f"{float(value):.6e}"
    return text
