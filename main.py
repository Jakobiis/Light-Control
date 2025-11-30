import asyncio
import signal
import threading
import sys
import time
from datetime import datetime
from config import load_config, reload_config, get_config, CONFIG_FILE
from bulb import discover_bulb
from monitor import init_sct, get_monitor_index
from color_utils import get_average_color_fast, rgb_to_hsv_vibrant
from gui import show_config_window, get_config_window
from watchfiles import awatch

stop_flag = False
sct = None

stats = {
    "start_time": None,
    "total_captures": 0,
    "last_update_time": 0,
    "fps_samples": [],
    "current_rgb": (0, 0, 0),
    "current_hsv": (0, 0, 0),
}


def update_debug_display():
    """Update the debug tab with current statistics"""
    config_window = get_config_window()

    if not config_window or not hasattr(config_window, "debug_widgets"):
        return

    try:
        current_time = time.time()
        if stats["last_update_time"] > 0:
            frame_time = current_time - stats["last_update_time"]
            if frame_time > 0:
                fps = 1.0 / frame_time
                stats["fps_samples"].append(fps)
                if len(stats["fps_samples"]) > 30:
                    stats["fps_samples"].pop(0)

        avg_fps = (
            sum(stats["fps_samples"]) / len(stats["fps_samples"])
            if stats["fps_samples"]
            else 0
        )

        if stats["start_time"]:
            uptime_seconds = int((datetime.now() - stats["start_time"]).total_seconds())
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"

        update_rate = (
            (time.time() - stats["last_update_time"]) * 1000
            if stats["last_update_time"] > 0
            else 0
        )

        config_window.update_debug_color(stats["current_rgb"], stats["current_hsv"])

        config_window.update_debug_stats(
            fps=avg_fps,
            update_rate=update_rate,
            total_captures=stats["total_captures"],
            uptime=uptime_str,
        )

    except Exception:
        pass


async def watch_config():
    """Watch config file for changes and reload automatically"""
    async for changes in awatch(CONFIG_FILE):
        reload_config()


async def main():
    global stop_flag, sct, stats

    try:
        load_config()
    except Exception as e:
        print(f"Failed to load config: {e}")
        print("Please create a bulb_config.json file or run config_gui.py")
        return

    config = get_config()
    if not config:
        print("Config is empty")
        return

    sct = init_sct()
    monitor_index = get_monitor_index(config)

    stats["start_time"] = datetime.now()
    stats["last_update_time"] = time.time()

    start_minimized = "--minimized" in sys.argv

    gui_thread = threading.Thread(
        target=show_config_window, args=(start_minimized,), daemon=True
    )
    gui_thread.start()

    bulb = await discover_bulb()
    if not bulb:
        return

    stop_event = asyncio.Event()

    def stop_signal(*_):
        global stop_flag, sct
        stop_flag = True
        stop_event.set()
        if sct:
            sct.close()
        print("\n👋 Bye!")

    signal.signal(signal.SIGINT, stop_signal)

    watcher_task = asyncio.create_task(watch_config())

    current_monitor = monitor_index

    try:
        while not stop_event.is_set():
            new_monitor = config["capture"].get("monitor_index", 1)
            if new_monitor != current_monitor:
                current_monitor = new_monitor

            r, g, b = get_average_color_fast(sct, current_monitor)
            h, s, v = rgb_to_hsv_vibrant(r, g, b)

            stats["current_rgb"] = (r, g, b)
            stats["current_hsv"] = (h, s, v)
            stats["total_captures"] += 1

            if stats["total_captures"] % 5 == 0:
                update_debug_display()

            stats["last_update_time"] = time.time()

            try:
                if bulb.modules.get("Light"):
                    transition_ms = config["capture"].get("transition_ms", 500)
                    await bulb.modules["Light"].set_hsv(
                        h, s, v, transition=transition_ms
                    )
            except Exception as e:
                print(f"Connection lost: {e}")
                bulb = await discover_bulb()
                if not bulb:
                    break

            await asyncio.sleep(config["capture"]["update_delay"])

    finally:
        watcher_task.cancel()
        if sct:
            sct.close()


if __name__ == "__main__":
    asyncio.run(main())
