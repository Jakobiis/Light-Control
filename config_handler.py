from config import save_config, reload_config


def save_configuration(entries):
    """Save all entries back to config and file"""
    try:
        for full_key, (entry, data_dict, key) in entries.items():
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
            return True, "Configuration Saved!"
        else:
            return False, "Failed to save configuration!"
    except Exception as e:
        return False, f"Error saving config: {e}"


def reload_configuration(entries):
    """Reload config from file and update UI"""
    try:
        if reload_config():
            for full_key, (entry, data_dict, key) in entries.items():
                entry.delete(0, "end")
                entry.insert(0, str(data_dict[key]))
            return True, "Configuration reloaded from file!"
        else:
            return False, "Configuration file unchanged."
    except Exception as e:
        return False, f"Error reloading config: {e}"
