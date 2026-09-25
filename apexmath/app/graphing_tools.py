"""Graphing and visualization tool for ApexMath."""

import io
import json
import re
import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from google.cloud import storage

# CRITICAL: Hardcode GCP Project ID as a string
PROJECT_ID = "qwiklabs-gcp-04-47563a3307b3"
BUCKET_NAME = "apexmath-visuals-47563a3307b3"

_storage_client = None


def get_storage_client() -> storage.Client:
    """Lazy initialize Cloud Storage client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def _preprocess_math_expression(expr: str) -> str:
    """Convert standard mathematical notation into valid Python/NumPy syntax."""
    cleaned = expr.strip()
    cleaned = cleaned.replace("^", "**")
    # Insert multiplication between numbers and variables/functions: 3x -> 3*x, 4sin -> 4*sin
    cleaned = re.sub(r"(\d)([a-zA-Z(])", r"\1*\2", cleaned)
    # Insert multiplication between closing parenthesis and variables/numbers/parentheses: (x)(x) -> (x)*(x)
    cleaned = re.sub(r"(\))([a-zA-Z0-9(])", r"\1*\2", cleaned)
    return cleaned


def _eval_func(expr_py: str, x_val: np.ndarray | float):
    """Safely evaluate expression with NumPy math functions."""
    safe_dict = {
        "x": x_val,
        "np": np,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "abs": np.abs,
        "pi": np.pi,
        "e": np.e,
        "arcsin": np.arcsin,
        "arccos": np.arccos,
        "arctan": np.arctan,
    }
    return eval(expr_py, {"__builtins__": {}}, safe_dict)


def plot_function(
    expression: str,
    x_min: float = -5.0,
    x_max: float = 5.0,
    tangent_at_x: float | None = None,
    second_expression: str = "",
    title: str = "",
) -> str:
    """Plot mathematical functions, curves, and tangent lines, returning a public visual image URL.

    Args:
        expression: Primary mathematical function to plot (e.g. 'x^3 - 3x', 'sin(x)', 'e^(-x^2)', 'x^2 - 4').
        x_min: Minimum x-value for the plot window (default: -5.0).
        x_max: Maximum x-value for the plot window (default: 5.0).
        tangent_at_x: Optional x-value where a tangent line should be plotted with its slope.
        second_expression: Optional second curve to plot (e.g. to compare two functions or show intersection).
        title: Optional plot title.

    Returns:
        JSON string containing the public image URL, markdown embed code, and plot details.
    """
    if x_min >= x_max:
        return json.dumps(
            {
                "error": f"Invalid range: x_min ({x_min}) must be strictly less than x_max ({x_max})."
            }
        )

    try:
        py_expr1 = _preprocess_math_expression(expression)
        x = np.linspace(x_min, x_max, 500)
        y = _eval_func(py_expr1, x)

        # Ensure y is an array matching x's shape
        if isinstance(y, (int, float)):
            y = np.full_like(x, y)

        fig, ax = plt.subplots(figsize=(8, 5))
        plot_title = title or f"Plot of $f(x) = {expression}$"

        ax.plot(x, y, label=f"$f(x) = {expression}$", color="#1a73e8", linewidth=2.2)

        # Plot optional second expression
        if second_expression.strip():
            py_expr2 = _preprocess_math_expression(second_expression)
            y2 = _eval_func(py_expr2, x)
            if isinstance(y2, (int, float)):
                y2 = np.full_like(x, y2)
            ax.plot(
                x,
                y2,
                label=f"$g(x) = {second_expression}$",
                color="#ea4335",
                linewidth=2.0,
                linestyle="--",
            )

        tangent_info = None
        # Plot optional tangent line
        if tangent_at_x is not None and x_min <= tangent_at_x <= x_max:
            h = 1e-5
            y0 = float(_eval_func(py_expr1, tangent_at_x))
            y_plus = float(_eval_func(py_expr1, tangent_at_x + h))
            y_minus = float(_eval_func(py_expr1, tangent_at_x - h))
            slope = (y_plus - y_minus) / (2 * h)

            # Tangent line equation: y_tan = slope * (x - tangent_at_x) + y0
            y_tan = slope * (x - tangent_at_x) + y0
            ax.plot(
                x,
                y_tan,
                label=f"Tangent at $x={tangent_at_x}$ ($m={slope:.2f}$)",
                color="#34a853",
                linewidth=1.8,
                linestyle=":",
            )
            ax.plot(
                tangent_at_x,
                y0,
                "ro",
                markersize=7,
                label=f"Point ({tangent_at_x}, {y0:.2f})",
            )
            tangent_info = {
                "x0": tangent_at_x,
                "y0": round(y0, 4),
                "slope": round(slope, 4),
                "equation": f"y - {y0:.2f} = {slope:.2f}(x - {tangent_at_x})",
            }

        # Styling
        ax.axhline(0, color="#5f6368", linewidth=0.9, linestyle="-")
        ax.axvline(0, color="#5f6368", linewidth=0.9, linestyle="-")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.set_title(plot_title, fontsize=13, pad=12)
        ax.set_xlabel("x", fontsize=11)
        ax.set_ylabel("y", fontsize=11)
        ax.legend(loc="best", framealpha=0.9)
        plt.tight_layout()

        # Save plot to in-memory buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", dpi=160)
        plt.close(fig)
        buffer.seek(0)

        # Upload to Google Cloud Storage
        client = get_storage_client()
        bucket = client.bucket(BUCKET_NAME)
        file_id = f"{uuid.uuid4().hex[:10]}"
        blob_path = f"graphs/{file_id}.png"
        blob = bucket.blob(blob_path)
        blob.upload_from_file(buffer, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        result = {
            "status": "success",
            "image_url": public_url,
            "markdown_embed": f"![{plot_title}]({public_url})",
            "expression": expression,
            "x_range": [x_min, x_max],
        }
        if tangent_info:
            result["tangent_details"] = tangent_info

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {"error": f"Failed to generate plot for '{expression}': {e!s}"}
        )
