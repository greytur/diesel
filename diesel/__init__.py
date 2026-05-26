# diesel/__init__.py
import dearpygui.dearpygui as dpg
import functools
import inspect

__INTERNAL_CONTEXT_ACTIVE = False

def __wrap_callable(name, func):
    """Dynamically wraps a callable to perform pre-call operations."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Pre-call operations
        print(f"[Diesel Pre-Call] About to call '{name}' with args={args} kwargs={kwargs}")
        # You can add any logic here before the call.
        if name == "create_context":
            global __INTERNAL_CONTEXT_ACTIVE
            __INTERNAL_CONTEXT_ACTIVE = True
        elif name == "destroy_context":
            global __INTERNAL_CONTEXT_ACTIVE
            __INTERNAL_CONTEXT_ACTIVE = False
        # Call the underlying function
        result = func(*args, **kwargs)
        
        # Optionally, add post-call operations here.
        return result

    # Preserve the original signature
    wrapper.__signature__ = inspect.signature(func)                                     # type: ignore
    return wrapper

def __getattr__(name):
    """
    Module-level __getattr__ intercepts attribute lookups.
    If the attribute is callable, we wrap it dynamically;
    otherwise, we return it directly.
    """
    attr = getattr(dpg, name)
    if callable(attr):
        # Return a dynamically wrapped version
        return __wrap_callable(name, attr)
    else:
        return attr

# Optionally, define __all__ to export all attributes from dpg
__all__ = dir(dpg)                                                                      # type: ignore