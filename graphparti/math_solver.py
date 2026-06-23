"""Math solver layer — SymPy integration for Graph Parti.

Type =expression in the Alt command line to evaluate.
Supports: arithmetic, algebra, calculus, solve, simplify, expand, factor.
"""
from __future__ import annotations


def solve_expression(text: str) -> str:
    """Evaluate a math expression via SymPy. Returns the result as a string.

    Input should NOT include the leading '=' prefix (caller strips it).
    Returns the result string, or an error message starting with 'Error:'.
    """
    try:
        import sympy
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
            convert_xor,
        )
        transformations = standard_transformations + (
            implicit_multiplication_application,
            convert_xor,
        )
        # Define common symbols
        local_dict = {}
        for name in ('x', 'y', 'z', 't', 'n', 'a', 'b', 'c'):
            local_dict[name] = sympy.Symbol(name)

        # Add common functions to namespace
        local_dict.update({
            'solve': sympy.solve,
            'diff': sympy.diff,
            'integrate': sympy.integrate,
            'simplify': sympy.simplify,
            'expand': sympy.expand,
            'factor': sympy.factor,
            'sqrt': sympy.sqrt,
            'sin': sympy.sin,
            'cos': sympy.cos,
            'tan': sympy.tan,
            'log': sympy.log,
            'ln': sympy.log,
            'exp': sympy.exp,
            'pi': sympy.pi,
            'e': sympy.E,
            'oo': sympy.oo,
            'limit': sympy.limit,
            'series': sympy.series,
            'Matrix': sympy.Matrix,
            'Rational': sympy.Rational,
            'abs': sympy.Abs,
        })

        result = parse_expr(text, local_dict=local_dict,
                            transformations=transformations)

        # If the result is evaluable to a number, also show the float
        try:
            numeric = float(result.evalf())
            exact = str(result)
            if exact != str(numeric):
                return f"{exact}  ({numeric:.6g})"
            return exact
        except (TypeError, AttributeError, ValueError):
            return str(result)
    except Exception as exc:
        return f"Error: {exc}"
