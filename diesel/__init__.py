# diesel/__init__.py
from __future__ import annotations

import functools
import inspect
from typing import Any, Callable
import dearpygui.dearpygui as _dpg
import functools
import inspect

_CONTEXT_ACTIVE = False
_WRAPPER_CACHE: dict[str, Callable[..., Any]] = {}

# >>> Diesel Public Functions

def is_context_active() -> bool:
    return _CONTEXT_ACTIVE


def hello_diesel() -> str:
    return "Hello from Diesel"


_DIESEL_EXPORTS = [
    "is_context_active",
    "hello_diesel",
]

def _wrap_callable(name: str, func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global _CONTEXT_ACTIVE

        if name == "create_context":
            _CONTEXT_ACTIVE = True
        elif name == "destroy_context":
            _CONTEXT_ACTIVE = False

        return func(*args, **kwargs)

    try:
        wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
    except (TypeError, ValueError):
        pass

    return wrapper


def __getattr__(name: str) -> Any:
    """
    Dynamically expose Dear PyGui attributes through Diesel.

    If the Dear PyGui attribute is callable, Diesel returns a wrapped version
    so pre-call behavior can run before the original function.
    Non-callable attributes are returned directly.
    """
    attr = getattr(_dpg, name)

    if not callable(attr):
        return attr

    cached = _WRAPPER_CACHE.get(name)
    if cached is not None:
        return cached

    wrapped = _wrap_callable(name, attr)
    _WRAPPER_CACHE[name] = wrapped
    return wrapped


_DPG_EXPORTS = [name for name in dir(_dpg) if not name.startswith("_")]

__all__ = [             # type: ignore
    *_DIESEL_EXPORTS,
    *_DPG_EXPORTS,
]