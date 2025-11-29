import customtkinter as ctk
from config import config, save_config, reload_config
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
import threading
import os
import platform
import subprocess

COLORS = {
    "bg": "#1a1f2e",
    "bg_secondary": "#242b3d",
    "accent": "#3d5a80",
    "accent_hover": "#4a6fa5",
    "text": "#e8eaed",
    "text_dim": "#9aa5b1",
    "border": "#2d3548",
}

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Platform-specific imports
if IS_WINDOWS:
    try:
        from windows_toasts import InteractableWindowsToaster, Toast

        interactableToaster = InteractableWindowsToaster(
            applicationText="Light Bulb Configurator",
        )
    except ImportError:
        interactableToaster = None
else:
    interactableToaster = None


def show_notification(message):
    """Cross-platform notification system"""
    if IS_WINDOWS and interactableToaster:
        newToast = Toast([message])
        interactableToaster.show_toast(newToast)
    elif IS_LINUX:
        try:
            subprocess.run(
                ["notify-send", "Smart Bulb Config", message], check=False, timeout=2
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"Notification: {message}")
    else:
        print(f"Notification: {message}")


class ConfigWindow:
    def __init__(self, start_minimized=False):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Smart Bulb Configuration")
        self.root.geometry("800x700")
        self.root.configure(fg_color=COLORS["bg"])

        self.entries = {}

        self.tray_icon = None
        self.start_minimized = start_minimized

        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)

        self._create_ui()
        self._create_tray_icon()

        # Start minimized if requested
        if self.start_minimized:
            self.root.after(100, self._hide_window)

    def _create_ui(self):
        """Build the configuration interface"""
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            main_frame,
            text="💡 Smart Bulb Configuration",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS["text"],
        )
        title.pack(pady=(0, 20))

        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=COLORS["bg_secondary"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["border"],
        )
        scroll_frame.pack(fill="both", expand=True)

        self._build_section(scroll_frame, "Color Boosts", config["color_boosts"])
        self._build_section(scroll_frame, "Weighting", config["weighting"])
        self._build_section(scroll_frame, "HSV Adjustments", config["hsv_adjustments"])
        self._build_section(scroll_frame, "Hue Adjustments", config["hue_adjustments"])
        self._build_section(scroll_frame, "Capture Settings", config["capture"])

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save Configuration",
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
            text="🔄 Reload from File",
            command=self._reload_config,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            corner_radius=10,
            height=45,
        )
        reload_btn.pack(side="left", expand=True, fill="x")

        startup_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        startup_frame.pack(fill="x", pady=(15, 0))

        # Create inner frame to center checkboxes
        checkbox_container = ctk.CTkFrame(startup_frame, fg_color="transparent")
        checkbox_container.pack(anchor="center")

        self.startup_var = ctk.BooleanVar(value=self._check_startup_exists())
        startup_check = ctk.CTkCheckBox(
            checkbox_container,
            text="🚀 Run on Startup",
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
            text="🔽 Launch Minimized to Tray",
            variable=self.minimized_var,
            command=self._toggle_launch_minimized,
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        minimized_check.pack(side="left", pady=5)

    def _build_section(self, parent, title, data_dict, prefix=""):
        """Build a configuration section"""
        section_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg"], corner_radius=12)
        section_frame.pack(fill="x", padx=15, pady=10)

        header = ctk.CTkLabel(
            section_frame,
            text=title,
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        header.pack(fill="x", padx=15, pady=(15, 10))

        for key, value in data_dict.items():
            row_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=5)

            label = ctk.CTkLabel(
                row_frame,
                text=self._format_label(key),
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

            self.entries[f"{title}.{key}"] = (entry, data_dict, key)

        ctk.CTkLabel(section_frame, text="", height=10).pack()

    def _format_label(self, key):
        """Convert snake_case to Title Case"""
        return key.replace("_", " ").title()

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
        """Show window from tray"""
        self.root.after(0, self.show_window)

    def _on_save_clicked(self, icon, item):
        """Save config from tray"""
        self.root.after(0, self._save_config)

    def _on_reload_clicked(self, icon, item):
        """Reload config from tray"""
        self.root.after(0, self._reload_config)

    def _on_exit_clicked(self, icon, item):
        """Exit application"""
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

                # Make run.sh executable if it exists
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

        # Re-create the startup entry with updated flags
        if IS_WINDOWS:
            self._toggle_startup_windows_minimized()
        elif IS_LINUX:
            self._toggle_startup_linux_minimized()

    def _toggle_startup_windows_minimized(self):
        """Update Windows startup shortcut with minimized flag"""
        autostart_path = self._get_autostart_path()

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

            status = "Enabled" if self.minimized_var.get() else "Disabled"
            show_notification(f"Launch Minimized {status}!")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to update startup shortcut: {e}", parent=self.root
            )
            self.minimized_var.set(not self.minimized_var.get())

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


def show_config_window(start_minimized=False):
    """Initialize and show the configuration window"""
    app = ConfigWindow(start_minimized=start_minimized)
    app.run()
    return app
