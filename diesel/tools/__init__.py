# diesel/tools/__init__.py

from .basic_utils import (
    int_time, hex_uuid, str_time,
    read_file, write_file,
    save_json, load_json,
    contains_any, capitalize_first_letter,
    remove_substrings, remove_prefixes, remove_suffixes,
    UniqueCounter,
)
from .logger_utils import (
    PadLvlWithFormatter, get_logger, USE_COLOR,
)
from .web_utils import (
    InvalidURLError, NoInternetConnectionError,
    is_internet_available, is_valid_url,
    download_url, fetch_url,
)
from .parsing_utils import (
    parse_color, hsl_to_rgb,
)


__all__ = [
    # diesel/tools/basic_utils.py
    "int_time", "hex_uuid", "str_time",                         # Basic Lambdas 
    "read_file", "write_file",                                  # Simple File Operations
    "save_json", "load_json",                                   # Json File Operations
    "contains_any", "capitalize_first_letter",                  # General-Purpose
    "remove_substrings", "remove_prefixes", "remove_suffixes",  # Remove from String Operations
    "UniqueCounter",                                            # Simple Counter Class
    # diesel/tools/web_utils.py
    "InvalidURLError", "NoInternetConnectionError",             # Validation Exceptions
    "is_internet_available", "is_valid_url",                    # Validation Functions
    "download_url", "fetch_url",                                # Download Functions
    # diesel/tools/logger_utils.py
    "PadLvlWithFormatter",                                      # Classes
    "get_logger",                                               # Functions
    "USE_COLOR",                                                # Constants
    # diesel/tools/parsing_utils.py
    "parse_color", "hsl_to_rgb",                                # Color Operations
]

# ---  DOCUMENT STATUS ---
# XXX: Currently Finalized