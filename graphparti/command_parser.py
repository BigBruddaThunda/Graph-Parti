"""Command parser — Lark grammar for the Alt command line.

Parses 'command [arg1] [arg2] ...' into structured dicts.
Math expressions (=...) are handled separately in canvas_widget.py.
"""
from __future__ import annotations

from lark import Lark, Transformer

COMMAND_GRAMMAR = r"""
    start: COMMAND_NAME (NUMBER)*

    COMMAND_NAME: /[a-zA-Z][a-zA-Z_]*/
    NUMBER: /\d+(\.\d+)?/

    %import common.WS
    %ignore WS
"""


class CommandTransformer(Transformer):
    def start(self, items):
        name = str(items[0]).lower()
        args = [float(t) if "." in str(t) else int(t) for t in items[1:]]
        return {"command": name, "args": args}

    def NUMBER(self, token):
        return token


_parser = Lark(COMMAND_GRAMMAR, parser='lalr')
_transformer = CommandTransformer()


def parse_command(text: str) -> dict | None:
    """Parse a command string into {"command": str, "args": list}.

    Returns None if parsing fails.

    Examples:
        parse_command("line")       -> {"command": "line", "args": []}
        parse_command("array 3 4")  -> {"command": "array", "args": [3, 4]}
        parse_command("fillet 0.5") -> {"command": "fillet", "args": [0.5]}
        parse_command("polygon 8")  -> {"command": "polygon", "args": [8]}
    """
    try:
        tree = _parser.parse(text.strip())
        return _transformer.transform(tree)
    except Exception:
        return None
