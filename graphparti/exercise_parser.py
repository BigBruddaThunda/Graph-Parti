"""Exercise notation parser — Lark grammar for workout shorthand.

Parses strings like '3x12 @185 RPE8' into structured dicts.
Context-aware: 3x12 means sets x reps here, not multiplication.

Examples
--------
parse_exercise("3x12")
    -> {"sets": 3, "reps": 12}

parse_exercise("3x12 @185 RPE8")
    -> {"sets": 3, "reps": 12, "load_weight": 185, "rpe": 8}

parse_exercise("Bench Press 3x10 @155")
    -> {"exercise": "Bench Press", "sets": 3, "reps": 10, "load_weight": 155}

parse_exercise("AMRAP 10min")
    -> {"protocol": "AMRAP", "duration": 10, "time_unit": "min"}

parse_exercise("5/3/1 @85%")
    -> {"scheme": [5, 3, 1], "load_percent": 85}
"""
from __future__ import annotations

from lark import Lark, Transformer

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

_GRAMMAR = r"""
start: (exercise_name WS+)? prescription

exercise_name: EXNAME (" " EXNAME)*

prescription: sets_reps (WS+ load)? (WS+ effort)?
            | timed_protocol

sets_reps: INT "x" INT            -> sets_reps
         | INT "x" INT "-" INT    -> sets_rep_range
         | INT ("/" INT)+         -> rep_scheme

load: "@" number PERCENT?         -> load

effort: RPE_TAG number            -> rpe
      | RIR_TAG number            -> rir

timed_protocol: AMRAP_TAG WS+ number TIME_UNIT  -> amrap
              | EMOM_TAG  WS+ number TIME_UNIT  -> emom

number: INT ("." INT)?

RPE_TAG  : /[Rr][Pp][Ee]/
RIR_TAG  : /[Rr][Ii][Rr]/
AMRAP_TAG: /[Aa][Mm][Rr][Aa][Pp]/
EMOM_TAG : /[Ee][Mm][Oo][Mm]/
PERCENT  : "%"
TIME_UNIT: /min|sec|s/

EXNAME: /[A-Za-z][A-Za-z'-]*/

%import common.INT
%import common.WS
"""

# ---------------------------------------------------------------------------
# Transformer — parse tree → structured dict
# ---------------------------------------------------------------------------


class _ExerciseTransformer(Transformer):
    """Convert a Lark parse tree into a plain dict."""

    # ---- top-level --------------------------------------------------------

    def start(self, items: list) -> dict:
        result: dict = {}
        for item in items:
            if isinstance(item, dict):
                result.update(item)
        return result

    def exercise_name(self, tokens) -> dict:
        # tokens are EXNAME Token objects; join them with spaces
        return {"exercise": " ".join(str(t) for t in tokens if str(t).strip())}

    def prescription(self, items: list) -> dict:
        result: dict = {}
        for item in items:
            if isinstance(item, dict):
                result.update(item)
        return result

    # ---- sets / reps ------------------------------------------------------

    def sets_reps(self, items) -> dict:
        return {"sets": int(items[0]), "reps": int(items[1])}

    def sets_rep_range(self, items) -> dict:
        return {
            "sets": int(items[0]),
            "reps_low": int(items[1]),
            "reps_high": int(items[2]),
        }

    def rep_scheme(self, items) -> dict:
        return {"scheme": [int(i) for i in items]}

    # ---- load -------------------------------------------------------------

    def load(self, items) -> dict:
        val = items[0]  # already a number (int or float)
        is_percent = any(str(t) == "%" for t in items[1:])
        if is_percent:
            return {"load_percent": val}
        return {"load_weight": val}

    # ---- effort -----------------------------------------------------------

    def rpe(self, items) -> dict:
        # items[0] may be RPE_TAG token; last item is the number
        return {"rpe": items[-1]}

    def rir(self, items) -> dict:
        return {"rir": items[-1]}

    # ---- timed protocols --------------------------------------------------

    def amrap(self, items) -> dict:
        # items contains: AMRAP_TAG token, WS token, number (int/float), TIME_UNIT token
        from lark.lexer import Token
        number_val = next(v for v in items if isinstance(v, (int, float)))
        time_unit = next(str(t) for t in items if isinstance(t, Token) and t.type == "TIME_UNIT")
        return {
            "protocol": "AMRAP",
            "duration": number_val,
            "time_unit": time_unit.lower(),
        }

    def emom(self, items) -> dict:
        from lark.lexer import Token
        number_val = next(v for v in items if isinstance(v, (int, float)))
        time_unit = next(str(t) for t in items if isinstance(t, Token) and t.type == "TIME_UNIT")
        return {
            "protocol": "EMOM",
            "duration": number_val,
            "time_unit": time_unit.lower(),
        }

    # ---- number -----------------------------------------------------------

    def number(self, items) -> int | float:
        if len(items) == 1:
            return int(items[0])
        return float(f"{items[0]}.{items[1]}")


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_parser = Lark(_GRAMMAR, parser="earley", ambiguity="resolve")
_transformer = _ExerciseTransformer()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_exercise(text: str) -> dict | None:
    """Parse exercise notation shorthand into a structured dict.

    Returns ``None`` if the input cannot be parsed.

    Parameters
    ----------
    text:
        Workout shorthand string, e.g. ``"3x12 @185 RPE8"`` or
        ``"Bench Press 3x10 @155"``.

    Returns
    -------
    dict | None
        Keys present depend on what was parsed:

        - ``sets``, ``reps`` — basic sets × reps
        - ``sets``, ``reps_low``, ``reps_high`` — rep range (e.g. ``4x8-12``)
        - ``scheme`` — slash-separated rep scheme (e.g. ``5/3/1``)
        - ``load_weight`` — absolute load in lbs/kg
        - ``load_percent`` — load as % of training max
        - ``rpe`` — rate of perceived exertion
        - ``rir`` — reps in reserve
        - ``protocol`` — ``"AMRAP"`` or ``"EMOM"``
        - ``duration``, ``time_unit`` — for timed protocols
        - ``exercise`` — exercise name prefix if present
    """
    try:
        tree = _parser.parse(text.strip())
        return _transformer.transform(tree)
    except Exception:
        return None
