"""
Monitor identification overlay system
Shows numbered cards on each monitor to help identify them
"""

import customtkinter as ctk
import threading
import time
from ui import COLORS


class MonitorIdentifier:
    """Manages identification overlays for monitors"""

    def __init__(self):
        self.overlay_windows = []
        self.is_showing = False

    def show_overlays(self, monitors_info, duration=3):
        """
        Show identification overlays on all monitors

        Args:
            monitors_info: List of monitor dictionaries with index, width, height, left, top
            duration: How long to show overlays in seconds (0 = until manually closed)
        """
        if self.is_showing:
            return

        self.is_showing = True

        for monitor in monitors_info:
            overlay = self._create_overlay(monitor)
            self.overlay_windows.append(overlay)

        if duration > 0:
            threading.Thread(
                target=self._auto_hide, args=(duration,), daemon=True
            ).start()

    def _create_overlay(self, monitor):
        """Create a single overlay window for a monitor"""
        overlay = ctk.CTkToplevel()
        overlay.attributes("-topmost", True)
        overlay.overrideredirect(True)  # Remove window decorations

        try:
            overlay.attributes("-transparentcolor", COLORS["bg"])
            overlay.configure(fg_color=COLORS["bg"])
        except Exception:
            pass

        card_width = 200
        card_height = 200
        x_pos = monitor["left"] + monitor["width"] - card_width - 40
        y_pos = monitor["top"] + 40

        overlay.geometry(f"{card_width}x{card_height}+{x_pos}+{y_pos}")

        card = ctk.CTkFrame(
            overlay,
            fg_color=COLORS["bg_secondary"],
            corner_radius=20,
            border_width=4,
            border_color=COLORS["accent"],
            width=card_width,
            height=card_height,
        )
        card.pack(fill="both", expand=True, padx=0, pady=0)
        card.pack_propagate(False)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        number_badge = ctk.CTkFrame(
            content, fg_color=COLORS["accent"], corner_radius=50, width=100, height=100
        )
        number_badge.pack(expand=True)
        number_badge.pack_propagate(False)

        number_label = ctk.CTkLabel(
            number_badge,
            text=str(monitor["index"]),
            font=("Segoe UI", 48, "bold"),
            text_color=COLORS["text"],
        )
        number_label.pack(expand=True)

        info_label = ctk.CTkLabel(
            content,
            text=f"Display {monitor['index']}",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["text"],
        )
        info_label.pack(pady=(10, 0))

        resolution_label = ctk.CTkLabel(
            content,
            text=f"{monitor['width']} × {monitor['height']}",
            font=("Segoe UI", 12),
            text_color=COLORS["text_dim"],
        )
        resolution_label.pack(pady=(5, 0))

        def close_all(e=None):
            self.hide_overlays()

        for widget in [
            card,
            number_badge,
            number_label,
            info_label,
            resolution_label,
            content,
        ]:
            try:
                widget.bind("<Button-1>", close_all)
            except Exception:
                pass

        return overlay

    def _auto_hide(self, duration):
        """Automatically hide overlays after duration"""
        time.sleep(duration)
        self.hide_overlays()

    def hide_overlays(self):
        """Hide and destroy all overlay windows"""
        if not self.is_showing:
            return

        for overlay in self.overlay_windows:
            try:
                overlay.destroy()
            except Exception:
                pass

        self.overlay_windows = []
        self.is_showing = False


_identifier = MonitorIdentifier()


def identify_monitors(monitors_info, duration=3):
    """
    Show identification overlays on all monitors

    Args:
        monitors_info: List of monitor dictionaries
        duration: How long to show overlays (0 = until clicked)
    """
    _identifier.show_overlays(monitors_info, duration)


def hide_monitor_overlays():
    """Hide any active monitor overlays"""
    _identifier.hide_overlays()
