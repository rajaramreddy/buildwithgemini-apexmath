"""Math calculation tool using the free public Newton Math API."""

import json
import urllib.parse
import urllib.request


def calculate_symbolic_math(operation: str, expression: str) -> str:
    """Compute symbolic mathematical operations using the public Newton Math API.

    Supported operations:
    - 'derive': Compute the derivative of a function (e.g. 'x^3 - 3x', 'sin(x)').
    - 'integrate': Compute the indefinite integral of a function (e.g. '2x', 'cos(x)').
    - 'tangent': Find the equation of the tangent line at point c (format: 'c|f(x)', e.g. '2|x^3').
    - 'zeroes': Find the roots/zeroes of a polynomial (e.g. 'x^2 - 4').
    - 'simplify': Simplify an algebraic expression (e.g. '2^2 + 2(2)').
    - 'factor': Factor a polynomial expression (e.g. 'x^2 + 2x').

    Args:
        operation: The operation ('derive', 'integrate', 'tangent', 'zeroes', 'simplify', 'factor').
        expression: The mathematical expression string.

    Returns:
        JSON string containing the operation, original expression, and computed result.
    """
    op = operation.strip().lower()
    valid_ops = {"derive", "integrate", "tangent", "zeroes", "simplify", "factor"}
    if op not in valid_ops:
        return json.dumps(
            {
                "error": f"Unsupported operation '{operation}'. Supported operations: {sorted(valid_ops)}"
            }
        )

    encoded_expr = urllib.parse.quote(expression.strip(), safe="")
    url = f"https://newton.vercel.app/api/v2/{op}/{encoded_expr}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ApexMath-Agent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return json.dumps(data, indent=2)
            return json.dumps(
                {"error": f"API request failed with status {resp.status}"}
            )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to compute {op} for '{expression}': {e!s}"}
        )
