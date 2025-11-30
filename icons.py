"""
Icon Loader for CustomTkinter
Loads PNG icons from the icons/ folder
For simplicity, uses PNG format to avoid SVG dependencies
"""

from pathlib import Path
from PIL import Image
import customtkinter as ctk

ICONS_DIR = Path(__file__).parent / "icons"

_icon_cache = {}


def load_icon(name, size=(20, 20)):
    """
    Load a PNG icon and return as CTkImage

    Args:
        name: Icon filename (with or without .png extension)
        size: Tuple of (width, height) in pixels

    Returns:
        CTkImage object ready for use in customtkinter widgets
    """
    if not any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
        name = f"{name}.png"

    cache_key = f"{name}_{size[0]}x{size[1]}"

    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    icon_path = ICONS_DIR / name

    if not icon_path.exists():
        print(f"Warning: Icon not found: {icon_path}")
        print("Please ensure PNG icons are in the icons/ folder")
        return None

    try:
        img = Image.open(icon_path)

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)

        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=size)

        _icon_cache[cache_key] = ctk_image

        return ctk_image

    except Exception as e:
        print(f"Error loading icon {name}: {e}")
        return None


class Icons:
    """Container for commonly used icons"""

    @staticmethod
    def settings(size=(20, 20)):
        return load_icon("settings", size)

    @staticmethod
    def monitor(size=(20, 20)):
        return load_icon("monitor", size)

    @staticmethod
    def save(size=(20, 20)):
        return load_icon("save", size)

    @staticmethod
    def reset(size=(20, 20)):
        return load_icon("reset", size)

    @staticmethod
    def check(size=(20, 20)):
        return load_icon("check", size)

    @staticmethod
    def close(size=(20, 20)):
        return load_icon("close", size)

    @staticmethod
    def info(size=(20, 20)):
        return load_icon("info", size)

    @staticmethod
    def warning(size=(20, 20)):
        return load_icon("warning", size)

    @staticmethod
    def search(size=(20, 20)):
        return load_icon("search", size)

    @staticmethod
    def refresh(size=(20, 20)):
        return load_icon("refresh", size)
