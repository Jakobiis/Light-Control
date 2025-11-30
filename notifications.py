import platform
import subprocess
from windows_toasts import InteractableWindowsToaster, Toast

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

interactableToaster = None
if IS_WINDOWS:
    try:
        interactableToaster = InteractableWindowsToaster(
            applicationText="Light Bulb Configurator"
        )
    except ImportError:
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
