import colorsys
import numpy as np
from config import get_config


def get_average_color_fast(sct, monitor_index):
    """Optimized color calculation with MSS and reduced operations"""
    config = get_config()

    try:
        monitor = sct.monitors[monitor_index]
        crop = config["capture"]["crop_percent"]
        w, h = monitor["width"], monitor["height"]

        capture_region = {
            "left": int(monitor["left"] + w * crop),
            "top": int(monitor["top"] + h * crop),
            "width": int(w * (1 - 2 * crop)),
            "height": int(h * (1 - 2 * crop)),
        }

        screenshot = sct.grab(capture_region)
        arr = np.array(screenshot, dtype=np.float32)[:, :, :3]
        arr = arr[:, :, ::-1]

        downsample = config["capture"].get("downsample", 4)
        if downsample > 1:
            arr = arr[::downsample, ::downsample, :]

        boosts = config["color_boosts"]
        arr[:, :, 0] *= boosts["red"]
        arr[:, :, 1] *= boosts["green"]
        arr[:, :, 2] *= boosts["blue"]
        arr = np.clip(arr, 0, 255)

        arr_norm = arr / 255.0
        r, g, b = arr_norm[:, :, 0], arr_norm[:, :, 1], arr_norm[:, :, 2]

        max_rgb = np.maximum(np.maximum(r, g), b)
        min_rgb = np.minimum(np.minimum(r, g), b)
        diff = max_rgb - min_rgb

        with np.errstate(divide="ignore", invalid="ignore"):
            saturation = np.where(max_rgb > 0, diff / max_rgb, 0)

        hue = np.zeros_like(r)
        mask = diff > 0

        with np.errstate(divide="ignore", invalid="ignore"):
            r_max = mask & (max_rgb == r)
            hue[r_max] = (60 * ((g[r_max] - b[r_max]) / diff[r_max]) + 360) % 360

            g_max = mask & (max_rgb == g)
            hue[g_max] = (60 * ((b[g_max] - r[g_max]) / diff[g_max]) + 120) % 360

            b_max = mask & (max_rgb == b)
            hue[b_max] = (60 * ((r[b_max] - g[b_max]) / diff[b_max]) + 240) % 360

        hue_config = config["hue_adjustments"]

        if hue_config["yellow_boost"] != 1.0:
            yellow_mask = (hue >= hue_config["yellow_hue_min"]) & (
                hue <= hue_config["yellow_hue_max"]
            )
            arr[yellow_mask, 0] *= hue_config["yellow_boost"]
            arr[yellow_mask, 1] *= hue_config["yellow_boost"]

        if hue_config["cyan_boost"] != 1.0:
            cyan_mask = (hue >= hue_config["cyan_hue_min"]) & (
                hue <= hue_config["cyan_hue_max"]
            )
            arr[cyan_mask, 1] *= hue_config["cyan_boost"]
            arr[cyan_mask, 2] *= hue_config["cyan_boost"]

        if hue_config["magenta_boost"] != 1.0:
            magenta_mask = (hue >= hue_config["magenta_hue_min"]) & (
                hue <= hue_config["magenta_hue_max"]
            )
            arr[magenta_mask, 0] *= hue_config["magenta_boost"]
            arr[magenta_mask, 2] *= hue_config["magenta_boost"]

        arr = np.clip(arr, 0, 255)

        luminance = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        w_config = config["weighting"]
        brightness_weight = (luminance / 255) ** w_config["brightness_power"]
        saturation_weight = saturation ** w_config["saturation_power"]

        weight = brightness_weight * saturation_weight * w_config["overall_multiplier"]
        weight[saturation < w_config["saturation_threshold"]] *= 0.1
        weight[luminance < w_config["luminance_threshold"]] = 0

        weight_3d = weight[:, :, np.newaxis]
        weighted = arr * weight_3d
        total_weight = np.sum(weight_3d)

        if total_weight > 0:
            avg_color = np.sum(weighted, axis=(0, 1)) / total_weight
            return tuple(avg_color.astype(int))
        else:
            return (0, 0, 0)

    except Exception as e:
        print(f"Error: {e}")
        return (0, 0, 0)


def rgb_to_hsv_vibrant(r, g, b):
    """Fast HSV conversion with gamma correction"""
    config = get_config()
    r, g, b = [(c / 255) ** 2.2 for c in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    hsv_config = config["hsv_adjustments"]
    s = min(
        s * hsv_config["saturation_multiplier"] + hsv_config["saturation_offset"], 1.0
    )
    v = min(
        max(
            v * hsv_config["value_multiplier"] + hsv_config["value_offset"],
            hsv_config["min_value"],
        ),
        1.0,
    )

    return int(h * 360), int(s * 100), int(v * 100)
