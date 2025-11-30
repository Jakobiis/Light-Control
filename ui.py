import customtkinter as ctk
from config import config
from icons import Icons, load_icon

COLORS = {
    "bg": "#0a0a0a",
    "bg_secondary": "#111111",
    "accent": "#333333",
    "accent_hover": "#444444",
    "text": "#e0e0e0",
    "text_dim": "#8a8a8a",
    "border": "#1a1a1a",
    "success": "#4e9f70",
    "active": "#666666",
    "tab_selected": "#333333",
    "tab_hover": "#444444",
    "card_selected": "#0a0a0a",
    "card_unselected": "#111111",
}


def build_settings_tab(parent, entries):
    """Build the settings tab with scrollable configuration"""
    scroll_frame = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        corner_radius=15,
    )
    scroll_frame.pack(fill="both", expand=True)

    sections = [
        ("Color Boosts", config["color_boosts"], "palette"),
        ("Weighting", config["weighting"], "sliders"),
        ("HSV Adjustments", config["hsv_adjustments"], "adjust"),
        ("Hue Adjustments", config["hue_adjustments"], "droplet"),
        ("Capture Settings", config["capture"], "monitor"),
    ]

    for title, data_dict, icon_name in sections:
        build_section(scroll_frame, title, data_dict, entries, icon_name)


def build_monitor_tab(
    parent,
    monitors_info,
    current_monitor,
    select_monitor_callback,
    identify_callback=None,
):
    """Build the monitor selection tab"""
    header_frame = ctk.CTkFrame(parent, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(20, 10))

    title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_row.pack(fill="x")

    title_label = ctk.CTkLabel(
        title_row,
        text="Select Display to Monitor",
        font=("Segoe UI", 22, "bold"),
        text_color=COLORS["text"],
        image=Icons.monitor(size=(28, 28)),
        compound="left",
    )
    title_label.pack(side="left")

    if identify_callback:
        identify_btn = ctk.CTkButton(
            title_row,
            text="Identify Displays",
            image=Icons.search(size=(18, 18)),
            compound="left",
            command=identify_callback,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            height=36,
            width=160,
        )
        identify_btn.pack(side="right")

    subtitle_label = ctk.CTkLabel(
        header_frame,
        text="Choose which display the smart bulb should sync with",
        font=("Segoe UI", 13),
        text_color=COLORS["text_dim"],
    )
    subtitle_label.pack(anchor="w", pady=(5, 0))

    monitors_container = ctk.CTkFrame(parent, fg_color="transparent")
    monitors_container.pack(fill="both", expand=True, padx=20, pady=20)

    if not monitors_info:
        error_label = ctk.CTkLabel(
            monitors_container,
            text="⚠️ No monitors detected",
            font=("Segoe UI", 16),
            text_color=COLORS["text_dim"],
        )
        error_label.pack(expand=True)
        return []

    sorted_monitors = sorted(monitors_info, key=lambda m: m["left"])
    cards_frame = ctk.CTkFrame(monitors_container, fg_color="transparent")
    cards_frame.pack(expand=True, fill="x")

    monitor_buttons = []
    for i, monitor in enumerate(sorted_monitors):
        card = create_monitor_card(
            cards_frame, monitor, current_monitor, i, select_monitor_callback
        )
        monitor_buttons.append((card, monitor["index"]))
        cards_frame.grid_columnconfigure(i, weight=1, uniform="equal")

    return monitor_buttons


def build_section(parent, title, data_dict, entries, icon_name=None):
    """Build a configuration section with optional icon"""
    section_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=12)
    section_frame.pack(fill="x", padx=15, pady=10)

    icon = load_icon(icon_name, size=(22, 22)) if icon_name else None

    header = ctk.CTkLabel(
        section_frame,
        text=title,
        font=("Segoe UI", 18, "bold"),
        text_color=COLORS["text"],
        anchor="w",
        image=icon,
        compound="left",
    )
    header.pack(fill="x", padx=15, pady=(15, 10))

    for key, value in data_dict.items():
        if key == "monitor_index":
            continue

        row_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=15, pady=5)

        label = ctk.CTkLabel(
            row_frame,
            text=format_label(key),
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        label.pack(side="left", fill="x", expand=True)

        entry = ctk.CTkEntry(
            row_frame,
            width=150,
            font=("Segoe UI", 13),
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            corner_radius=8,
        )
        entry.insert(0, str(value))
        entry.pack(side="right", padx=(10, 0))

        entries[f"{title}.{key}"] = (entry, data_dict, key)

    ctk.CTkLabel(section_frame, text="", height=10).pack()


def format_label(key):
    """Convert snake_case to Title Case"""
    return key.replace("_", " ").title()


def create_monitor_card(
    parent, monitor, current_monitor, index, select_monitor_callback
):
    """Create a visual card for each monitor"""
    is_selected = monitor["index"] == current_monitor

    card = ctk.CTkFrame(
        parent,
        fg_color=COLORS["card_selected"] if is_selected else COLORS["card_unselected"],
        corner_radius=15,
        border_width=3,
        border_color=COLORS["accent"] if is_selected else COLORS["border"],
        width=220,
        height=200,
    )
    card.grid(row=0, column=index, padx=10, pady=10, sticky="nsew")
    card.grid_propagate(False)

    card.bind("<Button-1>", lambda e: select_monitor_callback(monitor["index"]))

    content_frame = ctk.CTkFrame(card, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    content_frame.bind(
        "<Button-1>", lambda e: select_monitor_callback(monitor["index"])
    )

    badge_frame = ctk.CTkFrame(
        content_frame,
        fg_color=COLORS["accent"],
        corner_radius=10,
        width=70,
        height=70,
    )
    badge_frame.pack(pady=(0, 15))
    badge_frame.pack_propagate(False)
    badge_frame.bind("<Button-1>", lambda e: select_monitor_callback(monitor["index"]))

    badge_label = ctk.CTkLabel(
        badge_frame,
        text=str(monitor["index"]),
        font=("Segoe UI", 32, "bold"),
        text_color=COLORS["text"],
    )
    badge_label.pack(expand=True)
    badge_label.bind("<Button-1>", lambda e: select_monitor_callback(monitor["index"]))

    info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    info_frame.pack(fill="x")
    info_frame.bind("<Button-1>", lambda e: select_monitor_callback(monitor["index"]))

    monitor_name = ctk.CTkLabel(
        info_frame,
        text=f"Display {monitor['index']}",
        font=("Segoe UI", 16, "bold"),
        text_color=COLORS["text"],
    )
    monitor_name.pack()
    monitor_name.bind("<Button-1>", lambda e: select_monitor_callback(monitor["index"]))

    resolution_text = f"{monitor['width']} × {monitor['height']}"
    resolution_label = ctk.CTkLabel(
        info_frame,
        text=resolution_text,
        font=("Segoe UI", 13),
        text_color=COLORS["text_dim"],
    )
    resolution_label.pack(pady=(5, 0))
    resolution_label.bind(
        "<Button-1>", lambda e: select_monitor_callback(monitor["index"])
    )

    return card


def build_debug_tab(parent):
    """Build the debug/info tab with live information"""
    scroll_frame = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        corner_radius=15,
    )
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

    header = ctk.CTkLabel(
        scroll_frame,
        text="Debug Information",
        font=("Segoe UI", 22, "bold"),
        text_color=COLORS["text"],
        anchor="w",
    )
    header.pack(fill="x", pady=(0, 20))

    color_section = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg"], corner_radius=12)
    color_section.pack(fill="x", pady=(0, 15))

    color_header = ctk.CTkLabel(
        color_section,
        text="Current Color",
        font=("Segoe UI", 18, "bold"),
        text_color=COLORS["text"],
        anchor="w",
    )
    color_header.pack(fill="x", padx=15, pady=(15, 10))

    color_display_frame = ctk.CTkFrame(color_section, fg_color="transparent")
    color_display_frame.pack(fill="x", padx=15, pady=(0, 15))

    color_preview = ctk.CTkFrame(
        color_display_frame,
        fg_color="#000000",
        corner_radius=10,
        width=100,
        height=100,
        border_width=2,
        border_color=COLORS["border"],
    )
    color_preview.pack(side="left", padx=(0, 20))
    color_preview.pack_propagate(False)

    color_values_frame = ctk.CTkFrame(color_display_frame, fg_color="transparent")
    color_values_frame.pack(side="left", fill="both", expand=True)

    rgb_label = ctk.CTkLabel(
        color_values_frame,
        text="RGB: (0, 0, 0)",
        font=("Segoe UI", 14),
        text_color=COLORS["text"],
        anchor="w",
    )
    rgb_label.pack(anchor="w", pady=2)

    hsv_label = ctk.CTkLabel(
        color_values_frame,
        text="HSV: (0, 0, 0)",
        font=("Segoe UI", 14),
        text_color=COLORS["text"],
        anchor="w",
    )
    hsv_label.pack(anchor="w", pady=2)

    hex_label = ctk.CTkLabel(
        color_values_frame,
        text="HEX: #000000",
        font=("Segoe UI", 14),
        text_color=COLORS["text"],
        anchor="w",
    )
    hex_label.pack(anchor="w", pady=2)

    stats_section = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg"], corner_radius=12)
    stats_section.pack(fill="x", pady=(0, 15))

    stats_header = ctk.CTkLabel(
        stats_section,
        text="Statistics",
        font=("Segoe UI", 18, "bold"),
        text_color=COLORS["text"],
        anchor="w",
    )
    stats_header.pack(fill="x", padx=15, pady=(15, 10))

    stats_grid = ctk.CTkFrame(stats_section, fg_color="transparent")
    stats_grid.pack(fill="x", padx=15, pady=(0, 15))

    def create_stat_item(parent, label_text, value_text="0"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        label.pack(side="left", fill="x", expand=True)

        value = ctk.CTkLabel(
            frame,
            text=value_text,
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text"],
            anchor="e",
        )
        value.pack(side="right")

        return value

    fps_value = create_stat_item(stats_grid, "FPS:", "0")
    update_rate_value = create_stat_item(stats_grid, "Update Rate:", "0 ms")
    captures_value = create_stat_item(stats_grid, "Total Captures:", "0")
    uptime_value = create_stat_item(stats_grid, "Uptime:", "00:00:00")

    system_section = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg"], corner_radius=12)
    system_section.pack(fill="x", pady=(0, 15))

    system_header = ctk.CTkLabel(
        system_section,
        text="System Information",
        font=("Segoe UI", 18, "bold"),
        text_color=COLORS["text"],
        anchor="w",
    )
    system_header.pack(fill="x", padx=15, pady=(15, 10))

    system_grid = ctk.CTkFrame(system_section, fg_color="transparent")
    system_grid.pack(fill="x", padx=15, pady=(0, 15))

    monitor_value = create_stat_item(system_grid, "Active Monitor:", "1")
    resolution_value = create_stat_item(system_grid, "Resolution:", "0×0")

    return {
        "color_preview": color_preview,
        "rgb_label": rgb_label,
        "hsv_label": hsv_label,
        "hex_label": hex_label,
        "fps_value": fps_value,
        "update_rate_value": update_rate_value,
        "captures_value": captures_value,
        "uptime_value": uptime_value,
        "monitor_value": monitor_value,
        "resolution_value": resolution_value,
    }
