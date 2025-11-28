import json
import os

CONFIG_FILE = "bulb_config.json"

config = {}


def load_config():
    """Load config from file - no defaults"""
    global config
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Config file '{CONFIG_FILE}' not found. Please create it first."
        )

    try:
        with open(CONFIG_FILE, "r") as f:
            loaded_config = json.load(f)

        config.clear()
        config.update(loaded_config)

        print(f"✅ Loaded config from {CONFIG_FILE}")
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise Exception(f"Error loading config: {e}")


def save_config():
    """Save current config to file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"💾 Saved config to {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"⚠️ Error saving config: {e}")
        return False


def reload_config():
    """Reload config from file"""
    global config
    try:
        with open(CONFIG_FILE, "r") as f:
            new_config = json.load(f)

        if new_config != config:
            config.clear()
            config.update(new_config)
            print("🔄 Config reloaded!")
            return True
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in config file: {e}")
    except Exception as e:
        print(f"⚠️ Error reloading: {e}")
    return False


def get_config():
    """Get current config dictionary"""
    return config
