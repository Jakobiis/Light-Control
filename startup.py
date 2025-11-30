import os
import platform
from win32com.client import Dispatch

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def get_autostart_path():
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


def check_startup_exists():
    """Check if startup entry exists"""
    autostart_path = get_autostart_path()
    return autostart_path and os.path.exists(autostart_path)


def toggle_startup(enabled):
    """Toggle run on startup"""
    autostart_path = get_autostart_path()
    if enabled:
        try:
            if IS_WINDOWS:
                bat_path = os.path.abspath("run.bat")
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(autostart_path)
                shortcut.TargetPath = bat_path
                shortcut.Arguments = "--silent"
                shortcut.WorkingDirectory = os.path.dirname(bat_path)
                shortcut.save()
            elif IS_LINUX:
                script_path = os.path.abspath("run.sh")
                work_dir = os.path.dirname(script_path)
                exec_cmd = f"{script_path} --silent"
                desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Smart Bulb Screen Sync
Exec={exec_cmd}
Path={work_dir}
"""
                with open(autostart_path, "w") as f:
                    f.write(desktop_entry)
                os.chmod(autostart_path, 0o755)
        except Exception as e:
            print(f"Error creating autostart entry: {e}")
    else:
        if os.path.exists(autostart_path):
            os.remove(autostart_path)
