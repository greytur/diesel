# diesel/tools/basic_utils.py
# Basic Utilities
from typing import Any, Union, Iterable, Callable
import collections.abc
import json
import time
import uuid
import os


# >>> Basic Lambdas
int_time = lambda : int(time.time()) 
hex_uuid = lambda : uuid.uuid4().hex
str_time = lambda : str(int_time())     # str(int(time.time()))


# >>> Simple File Operations
def read_file(fpath: str) -> str:
    """ Reads a file's contents and returns them if the given file path exists.<br> Throws `FileNotFoundError` if path does not exist. """
    if not os.path.exists(fpath):
        raise FileNotFoundError(fpath)
    with open(fpath, 'r') as f:
        fdata = f.read()
    return fdata

def write_file(fpath: str, data: str) -> None:
    """ Writes the contents of `data` to `fpath`, it will attempt to create a file if it does not exist, and will overwrite a file if it does. """
    with open(fpath, 'w') as f:
        f.write(data)


# >>> JSON File Operations
def save_json(fpath: str, data: Any, *args, **kwargs) -> None:
    """ A `json.dumps` wrapper for `write_file`, writes the result of `json.dumps(data)` to `fpath`. """
    data = json.dumps(data, *args, **kwargs)
    write_file(fpath, data)

def load_json(fpath: str, *args, **kwargs) -> Any:
    """ A `json.loads` wrapper for `read_file`, loads `fpath` directly into `json.loads(data)` and returns the output. """
    data = read_file(fpath)
    return json.loads(data, *args, **kwargs)


# >>> General-Purpose Functions 
def contains_any(container: collections.abc.Iterable, items: Union[Any, Iterable]) -> bool:
    """ Check if the container contains any of the given item(s).

    Args:
        container: An iterable (like a list, set, or string) to search inside.
        items: A single item or an iterable of items to search for.
    """
    # FORMERLY KNOWN AS `any_in`
    if isinstance(items, collections.abc.Iterable) and not isinstance(items, str):
        return any(item in container for item in items)
    return items in container

def capitalize_first_letter(string: str) -> str:
    """ Returns the given string with the first letter capitalized, if the string is empty or is not a valid `str` type, it will return an empty string. """
    if string:
        return string[:1].upper() + string[1:]
    return ""


# >>> Remove From String Operations
def remove_prefixes(text: str, prefixes: Union[str, Iterable[str]]) -> str:
    """ Remove one or more prefixes from a string. <br>Note that substrings are removed in order given, thus **ORDER MATTERS**.

    Args:
        text: The string to process.
        prefixes: A single prefix or an iterable of prefixes.
    Returns:
        The text with the given prefix(es) removed.
    """
    if isinstance(prefixes, str):
        return text.removeprefix(prefixes)
    if isinstance(prefixes, Iterable):
        for prefix in prefixes:
            text = text.removeprefix(prefix)
        return text
    raise TypeError("`prefixes` must be a str or an iterable of str")

def remove_suffixes(text: str, suffixes: Union[str, Iterable[str]]) -> str:
    """ Remove one or more suffixes from a string. <br>Note that suffixes are removed in order given, thus **ORDER MATTERS**.
    
    Args:
        text: The string to process.
        suffixes: A single suffix or an iterable of suffixes.
    Returns:
        The text with the given suffix(es) removed.
    """
    if isinstance(suffixes, str):
        return text.removesuffix(suffixes)
    if isinstance(suffixes, Iterable):
        for suffix in suffixes:
            text = text.removesuffix(suffix)
        return text
    raise TypeError("`suffixes` must be a str or an iterable of str")

def remove_substrings(text: str, substrings: Union[str, Iterable[str]]) -> str:
    """ Remove one or more strings from a string. <br>Note that substrings are removed in order given, thus **ORDER MATTERS**.
    
    Args:
        text: The string to process.
        substrings: A single string or an iterable of strings.
    Returns:
        The text with the given substring(s) removed.
    """
    # Formerly known as `remove_all_from_str`
    if isinstance(substrings, str):
        return text.replace(substrings, "")
    if isinstance(substrings, Iterable):
        for substring in substrings:
            text = text.replace(substring, "")
        return text
    raise TypeError("`strings` must be a str or an iterable of str")


# >>> Basic Classes
class UniqueCounter:
    """ Creates a unique counter that can be incremeted, read, or reset. 

    - `get_next`: returns the current counter value and increments the counter
    - `get_counter`: returns the current counter value
    - `reset_counter`: resets the counter value to 0
    """
    def __init__(self):
        """ Initializes a new `UniqueCounter` with a count of `0`. """
        self._counter = 0
    
    def get_next(self) -> int:
        """ Returns the current integer count and increments the counter. """
        current = self._counter
        self._counter += 1
        return current
    
    def get_counter(self) -> int:
        """ Returns the current integer count. """
        return self._counter

    def reset_counter(self) -> None:
        """ Resets the integer count value to `0`. """
        self._counter = 0



__all__ = [
    "int_time", "hex_uuid", "str_time",                         # Basic Lambdas 
    "read_file", "write_file",                                  # Simple File Operations
    "save_json", "load_json",                                   # Json File Operations
    "contains_any", "capitalize_first_letter",                  # General-Purpose
    "remove_substrings", "remove_prefixes", "remove_suffixes",  # Remove from String Operations
    "UniqueCounter",                                            # Simple Counter Class
]

# ---  DOCUMENT STATUS ---
# XXX: Currently Finalized