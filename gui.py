import customtkinter as ctk
from config import config, save_config, reload_config
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
import threading
import os
import platform
from notifications import show_notification
import mss

from ui import build_settings_tab, build_monitor_tab, build_debug_tab, COLORS
from icons import Icons
from identify import identify_monitors

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


class ConfigWindow:
    def __init__(self, start_minimized=False):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Bulb Configuration")
        self.root.geometry("900x750")
        self.root.configure(fg_color=COLORS["bg"])
        self.root.minsize(800, 600)

        self.entries = {}
        self.monitor_buttons = []
        self.monitors_info = []
        self.debug_widgets = {}
        self.tray_icon = None
        self.start_minimized = start_minimized

        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)

        self._create_ui()
        self._create_tray_icon()

        if self.start_minimized:
            self.root.after(100, self._hide_window)

    def _get_monitors_info(self):
        """Get information about all available monitors"""
        try:
            with mss.mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors[1:], start=1):
                    monitors.append(
                        {
                            "index": i,
                            "width": monitor["width"],
                            "height": monitor["height"],
                            "left": monitor["left"],
                            "top": monitor["top"],
                        }
                    )
                return monitors
        except Exception as e:
            print(f"Error getting monitors: {e}")
            return []

    def _create_ui(self):
        """Build the configuration interface"""
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 20))

        title = ctk.CTkLabel(
            title_frame,
            text="Smart Bulb Configuration",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS["text"],
            image=Icons.settings(size=(32, 32)),
            compound="left",
        )
        title.pack()

        content_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_container.pack(fill="both", expand=True)

        tab_sidebar = ctk.CTkFrame(
            content_container,
            fg_color=COLORS["bg_secondary"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["border"],
            width=180,
        )
        tab_sidebar.pack(side="left", fill="y", padx=(0, 15))
        tab_sidebar.pack_propagate(False)

        self.tab_buttons = []
        self.current_tab = "display"

        tabs_data = [
            (
                "display",
                "Display",
                Icons.monitor(size=(20, 20)),
                self._show_display_tab,
            ),
            (
                "settings",
                "Settings",
                Icons.settings(size=(20, 20)),
                self._show_settings_tab,
            ),
            ("debug", "Debug", Icons.info(size=(20, 20)), self._show_debug_tab),
        ]

        tab_button_container = ctk.CTkFrame(tab_sidebar, fg_color="transparent")
        tab_button_container.pack(fill="both", expand=True, padx=10, pady=10)

        for tab_id, tab_text, tab_icon, tab_command in tabs_data:
            is_selected = tab_id == self.current_tab

            btn = ctk.CTkButton(
                tab_button_container,
                text=tab_text,
                image=tab_icon,
                compound="left",
                command=lambda tid=tab_id, cmd=tab_command: self._switch_tab(tid, cmd),
                font=("Segoe UI", 14, "bold"),
                fg_color=COLORS["tab_selected"] if is_selected else "transparent",
                hover_color=COLORS["tab_hover"],
                corner_radius=10,
                height=50,
                anchor="w",
                text_color=COLORS["text"],
            )
            btn.pack(fill="x", pady=5)
            self.tab_buttons.append((tab_id, btn))

        self.content_area = ctk.CTkFrame(
            content_container,
            fg_color=COLORS["bg_secondary"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["border"],
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        self.display_tab = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.settings_tab = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.debug_tab = ctk.CTkFrame(self.content_area, fg_color="transparent")

        self.monitors_info = self._get_monitors_info()
        current_monitor = config["capture"].get("monitor_index", 1)

        self.monitor_buttons = build_monitor_tab(
            self.display_tab,
            self.monitors_info,
            current_monitor,
            self._select_monitor,
            self._identify_monitors,
        )

        build_settings_tab(self.settings_tab, self.entries)
        self.debug_widgets = build_debug_tab(self.debug_tab)

        self._show_display_tab()

        self._create_bottom_buttons(main_frame)
        self._create_startup_options(main_frame)

    def _create_bottom_buttons(self, parent):
        """Create save and reload buttons"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Configuration",
            image=Icons.save(size=(20, 20)),
            compound="left",
            command=self._save_config,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=10,
            height=45,
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))

        reload_btn = ctk.CTkButton(
            btn_frame,
            text="Reload from File",
            image=Icons.refresh(size=(20, 20)),
            compound="left",
            command=self._reload_config,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            corner_radius=10,
            height=45,
        )
        reload_btn.pack(side="left", expand=True, fill="x")

    def _create_startup_options(self, parent):
        """Create startup checkboxes"""
        startup_frame = ctk.CTkFrame(parent, fg_color="transparent")
        startup_frame.pack(fill="x", pady=(15, 0))

        checkbox_container = ctk.CTkFrame(startup_frame, fg_color="transparent")
        checkbox_container.pack(anchor="center")

        self.startup_var = ctk.BooleanVar(value=self._check_startup_exists())
        startup_check = ctk.CTkCheckBox(
            checkbox_container,
            text="Run on Startup",
            variable=self.startup_var,
            command=self._toggle_startup,
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        startup_check.pack(side="left", padx=(0, 15), pady=5)

        self.minimized_var = ctk.BooleanVar(value=self._check_launch_minimized())
        minimized_check = ctk.CTkCheckBox(
            checkbox_container,
            text="Launch Minimized to Tray",
            variable=self.minimized_var,
            command=self._toggle_launch_minimized,
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        minimized_check.pack(side="left", pady=5)

    def _switch_tab(self, tab_id, tab_command):
        """Switch between tabs"""
        self.current_tab = tab_id

        for tid, btn in self.tab_buttons:
            if tid == tab_id:
                btn.configure(fg_color=COLORS["tab_selected"])
            else:
                btn.configure(fg_color="transparent")

        tab_command()

    def _show_display_tab(self):
        """Show the display tab"""
        self.settings_tab.pack_forget()
        self.debug_tab.pack_forget()
        self.display_tab.pack(fill="both", expand=True, padx=10, pady=10)

    def _show_settings_tab(self):
        """Show the settings tab"""
        self.display_tab.pack_forget()
        self.debug_tab.pack_forget()
        self.settings_tab.pack(fill="both", expand=True, padx=10, pady=10)

    def _show_debug_tab(self):
        """Show the debug tab"""
        self.display_tab.pack_forget()
        self.settings_tab.pack_forget()
        self.debug_tab.pack(fill="both", expand=True, padx=10, pady=10)
        self._update_debug_info()

    def _select_monitor(self, monitor_index):
        """Handle monitor selection"""
        config["capture"]["monitor_index"] = monitor_index

        for card, idx in self.monitor_buttons:
            is_selected = idx == monitor_index
            card.configure(
                fg_color=COLORS["card_selected"]
                if is_selected
                else COLORS["card_unselected"],
                border_color=COLORS["accent"] if is_selected else COLORS["border"],
            )
        self._save_config()

    def _identify_monitors(self):
        """Show identification overlays on all monitors"""
        if self.monitors_info:
            identify_monitors(self.monitors_info, duration=4)
        else:
            messagebox.showwarning(
                "No Monitors", "No monitors detected to identify.", parent=self.root
            )

    def _update_debug_info(self):
        """Update debug tab information"""
        if not self.debug_widgets:
            return

        current_monitor = config["capture"].get("monitor_index", 1)
        self.debug_widgets["monitor_value"].configure(text=str(current_monitor))

        for monitor in self.monitors_info:
            if monitor["index"] == current_monitor:
                res_text = f"{monitor['width']}×{monitor['height']}"
                self.debug_widgets["resolution_value"].configure(text=res_text)
                break

    def update_debug_color(self, rgb, hsv):
        """
        Update debug tab with current color
        Call this from your main capture loop

        Args:
            rgb: Tuple of (r, g, b) values 0-255
            hsv: Tuple of (h, s, v) values
        """
        if not self.debug_widgets:
            return

        try:
            hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            self.debug_widgets["color_preview"].configure(fg_color=hex_color)
            _rgb = ", ".join(map(str, rgb))
            self.debug_widgets["rgb_label"].configure(text=f"RGB: {_rgb}")
            self.debug_widgets["hsv_label"].configure(
                text=f"HSV: ({hsv[0]:.1f}, {hsv[1]:.1f}, {hsv[2]:.1f})"
            )
            self.debug_widgets["hex_label"].configure(text=f"HEX: {hex_color.upper()}")
        except Exception as e:
            print(f"Error updating debug color: {e}")

    def update_debug_stats(
        self, fps=0, update_rate=0, total_captures=0, uptime="00:00:00"
    ):
        """
        Update debug tab statistics
        Call this from your main capture loop

        Args:
            fps: Current frames per second
            update_rate: Update rate in milliseconds
            total_captures: Total number of captures
            uptime: Uptime string (HH:MM:SS)
        """
        if not self.debug_widgets:
            return

        try:
            self.debug_widgets["fps_value"].configure(text=f"{fps:.1f}")
            self.debug_widgets["update_rate_value"].configure(
                text=f"{update_rate:.0f} ms"
            )
            self.debug_widgets["captures_value"].configure(text=str(total_captures))
            self.debug_widgets["uptime_value"].configure(text=uptime)
        except Exception as e:
            print(f"Error updating debug stats: {e}")

    def _hide_window(self):
        """Hide window instead of closing it"""
        self.root.withdraw()
        show_notification("Config window minimized to tray")

    def show_window(self):
        """Show the window again"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _create_tray_icon(self):
        """Create system tray icon"""

        def create_icon_image():
            img = Image.new("RGB", (64, 64), color=(26, 31, 46))
            draw = ImageDraw.Draw(img)
            draw.ellipse([18, 12, 46, 40], fill=(61, 90, 128), outline=(232, 234, 237))
            draw.rectangle([26, 40, 38, 48], fill=(154, 165, 177))
            draw.rectangle([24, 48, 40, 52], fill=(154, 165, 177))
            return img

        menu = pystray.Menu(
            pystray.MenuItem("Show Config", self._on_show_clicked, default=True),
            pystray.MenuItem("Save Config", self._on_save_clicked),
            pystray.MenuItem("Reload Config", self._on_reload_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit_clicked),
        )

        icon_image = create_icon_image()
        self.tray_icon = pystray.Icon(
            "smart_bulb_config", icon_image, "Smart Bulb Config", menu
        )

        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def _on_show_clicked(self, icon, item):
        self.root.after(0, self.show_window)

    def _on_save_clicked(self, icon, item):
        self.root.after(0, self._save_config)

    def _on_reload_clicked(self, icon, item):
        self.root.after(0, self._reload_config)

    def _on_exit_clicked(self, icon, item):
        self.tray_icon.stop()
        self.root.quit()
        os._exit(0)

    def _get_autostart_path(self):
        """Get platform-specific autostart path"""
        if IS_WINDOWS:
            return os.path.join(
                os.environ["APPDATA"],
                "Microsoft\\Windows\\Start Menu\\Programs\\Startup",
                "SmartBulbSync.lnk",
            )
        elif IS_LINUX:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            return os.path.join(autostart_dir, "smart-bulb-sync.desktop")
        return None

    def _check_startup_exists(self):
        """Check if startup entry exists"""
        autostart_path = self._get_autostart_path()
        return autostart_path and os.path.exists(autostart_path)

    def _check_launch_minimized(self):
        """Check if launch minimized is enabled"""
        if IS_WINDOWS:
            autostart_path = self._get_autostart_path()
            if not os.path.exists(autostart_path):
                return False
            try:
                from win32com.client import Dispatch

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(autostart_path)
                return "--minimized" in shortcut.Arguments
            except Exception:
                return False
        elif IS_LINUX:
            autostart_path = self._get_autostart_path()
            if not os.path.exists(autostart_path):
                return False
            try:
                with open(autostart_path, "r") as f:
                    content = f.read()
                    return "--minimized" in content
            except Exception:
                return False
        return False

    def _toggle_startup(self):
        """Toggle run on startup"""
        if IS_WINDOWS:
            self._toggle_startup_windows()
        elif IS_LINUX:
            self._toggle_startup_linux()

    def _toggle_startup_windows(self):
        """Windows-specific startup toggle"""
        autostart_path = self._get_autostart_path()

        if self.startup_var.get():
            try:
                from win32com.client import Dispatch

                bat_path = os.path.abspath("run.bat")
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(autostart_path)
                shortcut.TargetPath = bat_path

                args = "--silent"
                if self.minimized_var.get():
                    args += " --minimized"
                shortcut.Arguments = args

                shortcut.WorkingDirectory = os.path.dirname(bat_path)
                shortcut.IconLocation = bat_path
                shortcut.save()

                show_notification("Run on Startup Enabled!")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to create startup shortcut: {e}", parent=self.root
                )
                self.startup_var.set(False)
        else:
            try:
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
                    show_notification("Run on Startup Disabled!")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to remove startup shortcut: {e}", parent=self.root
                )

    def _toggle_startup_linux(self):
        """Linux-specific startup toggle using .desktop file"""
        autostart_path = self._get_autostart_path()

        if self.startup_var.get():
            try:
                script_path = os.path.abspath("run.sh")
                work_dir = os.path.dirname(script_path)

                if os.path.exists(script_path):
                    os.chmod(script_path, 0o755)

                exec_cmd = f"{script_path} --silent"
                if self.minimized_var.get():
                    exec_cmd += " --minimized"

                desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Smart Bulb Screen Sync
Comment=Sync smart bulb with screen colors
Exec={exec_cmd}
Path={work_dir}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""

                with open(autostart_path, "w") as f:
                    f.write(desktop_entry)

                os.chmod(autostart_path, 0o755)
                show_notification("Run on Startup Enabled!")

            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to create autostart entry: {e}", parent=self.root
                )
                self.startup_var.set(False)
        else:
            try:
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
                    show_notification("Run on Startup Disabled!")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to remove autostart entry: {e}", parent=self.root
                )

    def _toggle_launch_minimized(self):
        """Toggle launch minimized option"""
        if not self.startup_var.get():
            messagebox.showwarning(
                "Startup Required",
                "Please enable 'Run on Startup' first!",
                parent=self.root,
            )
            self.minimized_var.set(False)
            return

        if IS_WINDOWS:
            self._toggle_startup_windows()
        elif IS_LINUX:
            self._toggle_startup_linux()

    def _save_config(self):
        """Save all entries back to config and file"""
        try:
            for full_key, (entry, data_dict, key) in self.entries.items():
                value_str = entry.get().strip()

                try:
                    if "." not in value_str:
                        value = int(value_str)
                    else:
                        value = float(value_str)
                except ValueError:
                    value = value_str

                data_dict[key] = value

            if save_config():
                show_notification("Configuration Saved!")
            else:
                messagebox.showerror(
                    "Error", "Failed to save configuration!", parent=self.root
                )

        except Exception as e:
            messagebox.showerror("Error", f"Error saving config: {e}", parent=self.root)

    def _reload_config(self):
        """Reload config from file and update UI"""
        try:
            if reload_config():
                for full_key, (entry, data_dict, key) in self.entries.items():
                    entry.delete(0, "end")
                    entry.insert(0, str(data_dict[key]))

                messagebox.showinfo(
                    "Success", "Configuration reloaded from file!", parent=self.root
                )
            else:
                messagebox.showwarning(
                    "No Changes", "Configuration file unchanged.", parent=self.root
                )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error reloading config: {e}", parent=self.root
            )

    def run(self):
        """Start the GUI"""
        self.root.mainloop()


_config_window_instance = None


def show_config_window(start_minimized=False):
    """Initialize and show the configuration window"""
    global _config_window_instance
    app = ConfigWindow(start_minimized=start_minimized)
    _config_window_instance = app
    app.run()
    return app


def get_config_window():
    """Get the current config window instance"""
    return _config_window_instance
