import mss


def init_sct():
    """Initialize the screen capture tool (MSS)"""
    return mss.mss()


def get_monitor_index(config):
    """Get monitor index from configuration"""
    return config["capture"].get("monitor_index", 1)
