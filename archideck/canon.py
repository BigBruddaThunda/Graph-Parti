"""SCL canon for the cockpit (mirrors system/scl/constants.yaml, SCL v5 — closed 61)."""

# 12 Operators (glyph, latin) — canon position order
OPERATORS = [
    ("📍", "pono"), ("🧲", "capio"), ("🤌", "facio"), ("👀", "specio"),
    ("🐋", "duco"), ("🧸", "fero"), ("🚀", "mitto"), ("🥨", "tendo"),
    ("🦢", "plico"), ("🦉", "logos"), ("🪵", "teneo"), ("✒️", "grapho"),
]

# 6 Axes (glyph, latin) — dial cycle order
AXES = [
    ("🏛", "Firmitas"), ("🔨", "Utilitas"), ("🌹", "Venustas"),
    ("🪐", "Gravitas"), ("⌛", "Temporitas"), ("🐬", "Sociatas"),
]

# 7 Orders (glyph, name)
ORDERS = [
    ("🐂", "Tuscan"), ("⛽", "Doric"), ("🦋", "Ionic"), ("🏟", "Corinthian"),
    ("🌾", "Composite"), ("⚖", "Vitruvian"), ("🖼", "Palladian"),
]

# 8 Colors (glyph, name, hex)
COLORS = [
    ("⚫", "Ordo", "#3C3C3C"), ("🟢", "Vigor", "#348219"), ("🔵", "Tectonics", "#2464E5"),
    ("🟣", "Rigor", "#9255E5"), ("🔴", "Prioritas", "#C1140C"), ("🟠", "Koinonia", "#F57E16"),
    ("🟡", "Mirabilia", "#F7B731"), ("⚪", "Otium", "#FFFFFF"),
]

# 5 Modifiers (glyph, name) — the Z-pad / tail
MODIFIERS = [("🛒", "Push"), ("🪡", "Pull"), ("🍗", "Legs"), ("➕", "Plus"), ("➖", "Ultra")]

# Axis row split around the copper [Archideck] nameplate
AXIS_LEFT = ["🏛", "⌛", "🔨"]
AXIS_RIGHT = ["🐬", "🌹", "🪐"]

COPPER = "#F5C2AF"  # Virgin Copper — nameplate + accent
