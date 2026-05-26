# diesel/tools/parsing_utils.py
# Parsing Utilities
from typing import Any, Union, Iterable, Callable
from pathlib import Path
import collections.abc
import colorsys
import json
import os
import re




def parse_color(value: Any) -> list[int]:
    """ Convert rgb(), rgba(), hsl(), hsla(), `list`, `tuple`, or packed int (`0xAABBGGRR`) to RGBA.,  

    Args:
        value: The color to parse.
    Returns:
        The parsed contents as a list of 4 integers.
    Raises:
        ValueError: If the parsed content is invalid/incorrect.
    """
    if isinstance(value, int):
        return [                 # 0x AA BB GG RR
            (value >> 0) & 255,  # Red      (bits    0-7)
            (value >> 8) & 255,  # Green    (bits   8-15)
            (value >> 16) & 255, # Blue     (bits  16-23)
            (value >> 24) & 255, # Alpha    (bits  24-32)
        ]

    if isinstance(value, (list, tuple)):
        values = list(value)
        if len(values) == 3:
            return [*values, 255]
        if len(values) == 4:
            return values

        raise ValueError(
            f"Expected color sequence of length 3 or 4, got {len(values)}."
        )

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("rgb"):
            nums = [int(num) for num in re.findall(r"\d+", stripped)]

            if len(nums) == 3:
                return [*nums, 255]

            if len(nums) == 4:
                return nums

            raise ValueError(
                f"Expected rgb()/rgba() with 3 or 4 values, got {value!r}."
            )

        if stripped.startswith("hsl"):
            nums = [float(num) for num in re.findall(r"[\d.]+", stripped)]

            if len(nums) not in {3, 4}:
                raise ValueError(
                    f"Expected hsl()/hsla() with 3 or 4 values, got {value!r}."
                )

            h, s, lightness = nums[0], nums[1], nums[2]
            alpha = nums[3] if len(nums) == 4 else 1.0
            return hsl_to_rgb(h, s, lightness, alpha)

    raise ValueError(f"Unsupported color value {value!r}.")


def hsl_to_rgb(hue: float, saturation: float, lightness: float, alpha: float = 1.0) -> list[int]:
    red, green, blue = colorsys.hls_to_rgb(
        hue / 360,
        lightness / 100,
        saturation / 100,
    )

    return [
        int(red * 255),
        int(green * 255),
        int(blue * 255),
        int(alpha * 255),
    ]



# # >>> Basic Lambdas
# int_time = lambda : int(time.time()) 
# hex_uuid = lambda : uuid.uuid4().hex
# str_time = lambda : str(int_time())     # str(int(time.time()))


# # >>> Simple File Operations
# def read_file(fpath: str | Path) -> str:
#     """ Reads a file's contents and returns them if the given file path exists.<br> Throws `FileNotFoundError` if path does not exist. """
#     if not os.path.exists(fpath):
#         raise FileNotFoundError(fpath)
#     with open(fpath, 'r') as f:
#         fdata = f.read()
#     return fdata

__all__ = [
    "parse_color", "hsl_to_rgb",                         # Basic Lambdas
]

# ---  DOCUMENT STATUS ---
# XXX: Currently Work in Progress