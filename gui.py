import customtkinter as ctk
from config import config, save_config, reload_config
from tkinter import messagebox
from windows_toasts import InteractableWindowsToaster, Toast
import pystray
from PIL import Image, ImageDraw
import threading
import os

COLORS = {
    "bg": "#1a1f2e",
    "bg_secondary": "#242b3d",
    "accent": "#3d5a80",
    "accent_hover": "#4a6fa5",
    "text": "#e8eaed",
    "text_dim": "#9aa5b1",
    "border": "#2d3548",
}

interactableToaster = InteractableWindowsToaster(
    applicationText="Light Bulb Configurator",
)


class ConfigWindow:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Smart Bulb Configuration")
        self.root.geometry("800x700")
        self.root.configure(fg_color=COLORS["bg"])

        self.entries = {}

        self.tray_icon = None

        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)

        self._create_ui()
        self._create_tray_icon()

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

        self.startup_var = ctk.BooleanVar(value=self._check_startup_exists())
        startup_check = ctk.CTkCheckBox(
            startup_frame,
            text="🚀 Run on Windows Startup",
            variable=self.startup_var,
            command=self._toggle_startup,
            font=("Segoe UI", 13),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        startup_check.pack(pady=5)

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
        newToast = Toast(["Config window minimized to tray"])
        interactableToaster.show_toast(newToast)

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

    def _check_startup_exists(self):
        """Check if startup shortcut exists"""
        startup_folder = os.path.join(
            os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        )
        shortcut_path = os.path.join(startup_folder, "SmartBulbSync.lnk")
        return os.path.exists(shortcut_path)

    def _toggle_startup(self):
        """Toggle run on startup"""
        startup_folder = os.path.join(
            os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        )
        shortcut_path = os.path.join(startup_folder, "SmartBulbSync.lnk")

        if self.startup_var.get():
            try:
                from win32com.client import Dispatch

                bat_path = os.path.abspath("run.bat")

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.TargetPath = bat_path
                shortcut.Arguments = "--silent"
                shortcut.WorkingDirectory = os.path.dirname(bat_path)
                shortcut.IconLocation = bat_path
                shortcut.save()

                newToast = Toast(["Run on Startup Enabled!"])
                interactableToaster.show_toast(newToast)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to create startup shortcut: {e}", parent=self.root
                )
                self.startup_var.set(False)
        else:
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    newToast = Toast(["Run on Startup Disabled!"])
                    interactableToaster.show_toast(newToast)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to remove startup shortcut: {e}", parent=self.root
                )

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
                newToast = Toast(["Configuration Saved!"])
                interactableToaster.show_toast(newToast)
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


def show_config_window():
    """Initialize and show the configuration window"""
    app = ConfigWindow()
    app.run()
    return app


if __name__ == "__main__":
    from config import load_config

    try:
        load_config()
        show_config_window()
    except Exception as e:
        print(f"Error: {e}")
