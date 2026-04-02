# diesel/tools/web_utils.py
# Web Utilities
import os
import re
import subprocess
import urllib.request
from typing import Union
from .basic_utils import write_file, read_file


# >>> Definitions
url_regex = (
    r'https?://(?:[a-z0-9-]+\.)+[a-z]{2,}'      # Required DOMAIN
    r'(?::\d+)?'                                # Optional PORT
    r'(?:/[^\s?#]*)?'                           # Optional PATH
    r'(?:\?[^\s#]*)?'                           # Optional QUERY
    r'(?:\#[^\s]*)?'                            # Optional FRAGMENT
)


# >>> Custom exceptions
class InvalidURLError(ValueError):
    """ Raised when a URL is invalid. """
    pass

class NoInternetConnectionError(ConnectionError):
    """ Raised when an internet connection is unavailable. """
    pass


# >>> Connection Utilities
def is_internet_available(timeout: int = 2) -> bool:
    """ Check if there is an active internet connection.

    Args:
        timeout: Timeout in seconds for the check (default timeout of 2 seconds).
    Returns:
        True if internet is available, False otherwise.
    """
    try:
        urllib.request.urlopen("https://www.google.com", timeout=timeout)
        return True
    except Exception:
        return False


# >>> URL Utilities 
def is_valid_url(url: str) -> bool:
    """ Return True if `url` is a valid URL. """
    return bool(re.fullmatch(url_regex, url, re.IGNORECASE))

def download_url(url: str) -> str:
    """ Download the contents of a URL as a string using `curl -sL`. 

    Args:
        url: The URL to download.
    Returns:
        The contents of the URL as a string.
    Raises:
        InvalidURLError: If the URL is invalid.
        ValueError: If the downloaded content is empty.
    """
    if not is_valid_url(url):
        raise InvalidURLError(url)
    result = subprocess.run(
        ["curl", "-sL", url], 
        capture_output=True, text=True, check=True
    )
    contents = result.stdout
    if not contents:
        raise ValueError("Downloaded content is empty.")
    return contents

def fetch_url(
    url: str,
    cache_dir: Union[str, None] = None,
    filename: Union[str, None] = None,
    use_cache: bool = True
) -> str:
    """ Fetch the contents of a URL as a string, optionally caching locally.

    Args:
        url: The URL to fetch.
        cache_dir: Directory to cache the downloaded file. If **None**, no caching is used.
        filename: Optional filename to store the cached file. Defaults to the basename of the URL.
        use_cache: If True, use cached file if available. Default is True.
    Returns:
        The contents of the URL as a string.
    Raises:
        NoInternetConnectionError: If there is no internet connection.
        FileNotFoundError: If `cache_dir` does not exist.
        NotADirectoryError: If `cache_dir` is not a directory.
    """
    # Attempt download with caching
    if cache_dir and use_cache:
        if not os.path.exists(cache_dir):
            raise FileNotFoundError(cache_dir)
        if not os.path.isdir(cache_dir):
            raise NotADirectoryError(cache_dir)

        if filename is None or not filename:
            filename = os.path.basename(url)
        target_path = os.path.join(cache_dir, filename)

        if use_cache and os.path.exists(target_path):
            return read_file(target_path)

        if not is_internet_available():
            raise NoInternetConnectionError("No internet connection available.")

        data = download_url(url)
        write_file(target_path, data)
        return data

    # Download without any caching 
    if not is_internet_available():
        raise NoInternetConnectionError("No internet connection available.")
    return download_url(url)


__all__ = [
    "InvalidURLError", "NoInternetConnectionError", # Validation Exceptions
    "is_internet_available", "is_valid_url",        # Validation Functions
    "download_url", "fetch_url"                     # Download Functions
]

# ---  DOCUMENT STATUS ---
# XXX: Currently Finalized