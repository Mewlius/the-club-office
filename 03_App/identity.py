"""Visual identity of a career: logo, banner, main and second colour.

Everything is optional: a career without settings keeps the default look.
Stored in assets/careers/<career>/ (never on GitHub):
    theme.json      {"primary": "#7A263A", "secondary": "#F5D90A", "logo": "logo.png", "banner": "banner.jpg"}
    logo.<ext>      PNG, JPG or WEBP
    banner.<ext>
The app's own logo, assets/app/logo.<ext>, is used for a career without logo.

Any colour can be chosen: the app adjusts it so that the text stays readable
(WCAG contrast). The main colour gives the header (dark enough for white text)
and a very pale page background; the second colour gives the highlights and the
big figures (dark enough to read on white, light enough to show on the header).
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

import settings

# Shortcuts in the Identity window (any other colour can be typed)
SWATCHES = [
    ("Navy", "#15233F"), ("Royal blue", "#1D4ED8"), ("Sky blue", "#38BDF8"), ("Claret", "#7A263A"),
    ("Red", "#DC2626"), ("Green", "#16A34A"), ("Dark green", "#14532D"), ("Purple", "#6D28D9"),
    ("Orange", "#EA580C"), ("Gold", "#D4A017"), ("Black", "#111111"),
]

IMAGE_KINDS = ("logo", "banner")
IMAGE_EXTENSIONS = (".png", ".jpg", ".webp")
MAX_IMAGE_BYTES = 5 * 1024 * 1024

WHITE = "#FFFFFF"
BLACK = "#000000"

# The default look (theme.py): used for everything a career does not set
DEFAULT_COLOURS = {
    "header": "#15233F",          # header background
    "paper": "#F3F5F8",           # page background
    "nav": "#FFFFFF",             # underline of the active page in the menu
    "figures": "#15233F",         # big figures (Home, records)
    "highlight": "#1F7A4D",       # the club's row, selected rows (bar and text)
    "highlight_soft": "#E6F0EA",  # the club's row, selected rows (background)
    "primary": "#15233F",         # Quasar primary: chosen buttons (competition, Overall...)
}

URL_CAREERS = "/career-assets"
URL_APP = "/app-assets"


# ----------------------------------------------------------------------
# Colours
# ----------------------------------------------------------------------

def parse_colour(text) -> str | None:
    """"#7a263a", "7A263A" or "#7a2" -> "#7A263A" (None when it is not a colour)."""
    match = re.fullmatch(r"#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", (text or "").strip())
    if not match:
        return None
    value = match.group(1)
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return "#" + value.upper()


def _rgb(colour: str) -> tuple[int, int, int]:
    return int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)


def _hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def mix(colour: str, other: str, share: float) -> str:
    """colour with a share (0 to 1) of other."""
    a, b = _rgb(colour), _rgb(other)
    return _hex(x + (y - x) * share for x, y in zip(a, b))


def luminance(colour: str) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in _rgb(colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio, from 1 (same) to 21 (black on white)."""
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _move_until(colour: str, towards: str, against: str, minimum: float) -> str:
    """Moves the colour towards black or white, a little at a time, until its
    contrast with "against" reaches the minimum."""
    result = colour
    share = 0.0
    while contrast(result, against) < minimum and share < 1:
        share = min(1.0, share + 0.04)
        result = mix(colour, towards, share)
    return result


def colours(theme: dict | None) -> dict:
    """The colours of the pages for a theme (the default look for what is not set)."""
    result = dict(DEFAULT_COLOURS)
    theme = theme or {}
    primary = parse_colour(theme.get("primary"))
    secondary = parse_colour(theme.get("secondary"))

    if primary:
        result["header"] = _move_until(primary, BLACK, WHITE, 4.5)  # white text on the header
        result["paper"] = mix(primary, WHITE, 0.93)                  # 7 % of the colour

    if secondary:
        accent = _move_until(secondary, BLACK, WHITE, 4.5)          # read on white, white text on it
        result["figures"] = accent
        result["highlight"] = accent
        result["primary"] = accent
        result["highlight_soft"] = mix(secondary, WHITE, 0.85)
        result["nav"] = _move_until(secondary, WHITE, result["header"], 3.0)  # seen on the header

    return result


def header_overlay(header: str, alpha: float = 0.78) -> str:
    """The header colour, see-through, laid over the banner so that the text stays readable."""
    r, g, b = _rgb(header)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ----------------------------------------------------------------------
# theme.json
# ----------------------------------------------------------------------

def _check_folder(folder: str) -> None:
    if not folder or folder in (".", "..") or Path(folder).name != folder:
        raise ValueError(f"not a career folder: {folder!r}")


def career_assets(folder: str) -> Path:
    _check_folder(folder)
    return settings.careers_assets_dir() / folder


def load_theme(folder: str) -> dict:
    """The career's theme.json ({} when there is none or it cannot be read)."""
    try:
        theme = json.loads((career_assets(folder) / "theme.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return theme if isinstance(theme, dict) else {}


def save_theme(folder: str, theme: dict) -> None:
    """Atomic write: a .tmp file first, then it replaces the old one."""
    directory = career_assets(folder)
    directory.mkdir(parents=True, exist_ok=True)
    clean = {key: value for key, value in theme.items() if value}
    tmp = directory / "theme.json.tmp"
    tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(directory / "theme.json")


def set_colours(folder: str, primary: str | None, secondary: str | None) -> dict:
    theme = load_theme(folder)
    theme["primary"] = parse_colour(primary)
    theme["secondary"] = parse_colour(secondary)
    save_theme(folder, theme)
    return theme


# ----------------------------------------------------------------------
# Images
# ----------------------------------------------------------------------

def image_extension(data: bytes) -> str | None:
    """.png, .jpg or .webp from the first bytes of the file (None for anything else)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def set_image(folder: str, kind: str, data: bytes) -> str:
    """Saves the logo or the banner of a career. Raises ValueError for a file
    that is not a PNG, JPG or WEBP image, or that is too big."""
    if kind not in IMAGE_KINDS:
        raise ValueError(f"unknown image: {kind}")
    extension = image_extension(data)
    if extension is None:
        raise ValueError("choose a PNG, JPG or WEBP image")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"the image is too big (more than {MAX_IMAGE_BYTES // (1024 * 1024)} MB)")

    directory = career_assets(folder)
    directory.mkdir(parents=True, exist_ok=True)
    name = kind + extension
    tmp = directory / (name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(directory / name)

    for other in IMAGE_EXTENSIONS:  # the previous image in another format
        if other != extension:
            (directory / (kind + other)).unlink(missing_ok=True)

    theme = load_theme(folder)
    theme[kind] = name
    save_theme(folder, theme)
    return name


def remove_image(folder: str, kind: str) -> None:
    if kind not in IMAGE_KINDS:
        raise ValueError(f"unknown image: {kind}")
    theme = load_theme(folder)
    theme.pop(kind, None)
    save_theme(folder, theme)
    for extension in IMAGE_EXTENSIONS:
        (career_assets(folder) / (kind + extension)).unlink(missing_ok=True)


def _url(base: str, path: Path, relative: str) -> str:
    return f"{base}/{quote(relative)}?v={int(path.stat().st_mtime)}"


def image_url(folder: str, kind: str) -> str | None:
    """The career's logo or banner, for the pages (None when there is none)."""
    name = load_theme(folder).get(kind)
    if not name or Path(name).name != name:
        return None
    path = career_assets(folder) / name
    return _url(URL_CAREERS, path, f"{folder}/{name}") if path.is_file() else None


def app_logo_url() -> str | None:
    """assets/app/logo.png (or .jpg, .webp): the logo of The Club Office, if there is one."""
    for extension in IMAGE_EXTENSIONS + (".jpeg",):
        path = settings.app_assets_dir() / ("logo" + extension)
        if path.is_file():
            return _url(URL_APP, path, path.name)
    return None


def logo_url(folder: str) -> str | None:
    """The career's logo, or the app's logo, or None."""
    return image_url(folder, "logo") or app_logo_url()
