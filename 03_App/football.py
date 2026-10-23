"""Football vocabulary shared by the pages: positions, squad roles, feet."""

# Position group of each position: goalkeeper, defence, midfield, attack
POSITION_GROUPS = {
    "GK": "gk",
    "SW": "def", "RWB": "def", "RB": "def", "RCB": "def", "CB": "def", "LCB": "def", "LB": "def", "LWB": "def",
    "RDM": "mid", "CDM": "mid", "LDM": "mid", "RM": "mid", "RCM": "mid", "CM": "mid", "LCM": "mid",
    "LM": "mid", "RAM": "mid", "CAM": "mid", "LAM": "mid",
    "RF": "att", "CF": "att", "LF": "att", "RW": "att", "RS": "att", "ST": "att", "LS": "att", "LW": "att",
}

# Usual squad sheet order: goalkeepers, then defence, midfield, attack
POSITION_ORDER = [
    "GK", "SW", "RWB", "RB", "RCB", "CB", "LCB", "LB", "LWB", "RDM", "CDM", "LDM", "RM", "RCM", "CM",
    "LCM", "LM", "RAM", "CAM", "LAM", "RF", "CF", "LF", "RW", "RS", "ST", "LS", "LW",
]

ROLE_ORDER = ["Crucial", "Important", "Rotation", "Sporadic", "Prospect"]

FOOT = {1: "Right", 2: "Left"}


def position_group(position) -> str:
    return POSITION_GROUPS.get(position or "", "mid")


def position_rank(position) -> int:
    return POSITION_ORDER.index(position) if position in POSITION_ORDER else 99


def role_rank(role) -> int:
    return ROLE_ORDER.index(role) if role in ROLE_ORDER else 99
