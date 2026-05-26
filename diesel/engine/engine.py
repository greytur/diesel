# diesel/engine/engine.py
"""
DIESEL runtime engine.

Loads a YAML DSL document, resolves names through the aggregator metadata artifact,
and compiles theme specs into DearPyGUI theme objects.

Direct execution path:

    python ./diesel engine

This file should not perform work at import time.
"""

from __future__ import annotations

import colorsys
import re
from pathlib import Path
from typing import Any, Mapping

import dearpygui.dearpygui as dpg
import yaml

from builder.aggregator import get_style_num_args
from config import (
    DEFAULT_AGGREGATOR_OUTPUT_PATH,
    DEFAULT_ENGINE_OUTPUT_PATH,
    DEFAULT_INPUT_PATH,
)
from tools import load_json, read_file, save_json, parse_color, hsl_to_rgb


LookupTable = dict[str, dict[str, dict[str, Any]]]
ThemeCompileResult = dict[str, Any]


# -----------------------------------------------------------------------------
# Errors
# -----------------------------------------------------------------------------


class DieselEngineError(Exception):
    """Base error for runtime DSL compilation."""


class InvalidComponentError(DieselEngineError, SyntaxError):
    """Raised when a theme component DSL name is unavailable."""


class InvalidThemingTargetError(DieselEngineError, SyntaxError):
    """Raised when a style/color DSL name is unavailable."""


class InvalidThemeValueError(DieselEngineError, ValueError):
    """Raised when a theme style/color value cannot be compiled."""


# -----------------------------------------------------------------------------
# YAML loading
# -----------------------------------------------------------------------------


def load_yaml(path: str | Path) -> dict[str, Any]:
    raw_text = read_file(Path(path))
    loaded_data = yaml.safe_load(raw_text)

    if loaded_data is None:
        return {}

    if not isinstance(loaded_data, dict):
        raise TypeError(
            f"Expected YAML root to be a mapping, got {type(loaded_data).__name__}."
        )

    return loaded_data


# TODO: Eventually this should accept `themes`, not `$themes`, once the DSL shape settles.
def extract_theme_specs(config: Mapping[str, Any]) -> dict[str, Any]:
    theme_specs = config.get("$themes", {})

    if not isinstance(theme_specs, dict):
        raise TypeError("Expected `$themes` to be a mapping.")

    return theme_specs


# -----------------------------------------------------------------------------
# Aggregator metadata lookup
# -----------------------------------------------------------------------------


def build_lookup_table(
    metadata_path: str | Path = DEFAULT_AGGREGATOR_OUTPUT_PATH,
) -> LookupTable:
    """
    Build runtime lookup tables from the aggregator metadata artifact.

    The compiler wants fast DSL-name lookup:

        lookup["component"][dsl_component_name]
        lookup["theming"][dsl_style_or_color_name]
    """
    metadata = load_json(Path(metadata_path))
    raws = metadata.get("raws", {})

    component_records = (
        raws.get("item")
        or raws.get("widget")
        or raws.get("component")
        or []
    )
    style_records = raws.get("style", [])
    color_records = raws.get("color", [])

    component_lookup: dict[str, dict[str, Any]] = {
        "$default": {
            "idnum": 0,
            "value": 0,
            "dpg": "mvAll",
        }
    }

    style_lookup: dict[str, dict[str, Any]] = {}
    color_lookup: dict[str, dict[str, Any]] = {}

    for record in component_records:
        dsl_name = record["dsl"]
        component_lookup[dsl_name] = {
            "idnum": record["idnum"],
            "value": record["dpg_value"],
            "dpg": record["dpg"],
        }

    for record in style_records:
        traits = record.get("traits") or {}
        num_args = traits.get("num_args")

        if num_args is None:
            num_args = get_style_num_args(
                record["im_name"],
                record["category"],
                record["dpg_value"],
            )

        style_lookup[record["dsl"]] = {
            "idnum": record["idnum"],
            "value": record["dpg_value"],
            "kind": record["kind"],
            "dpg": record["dpg"],
            "category": record["category"],
            "num_args": num_args,
        }

    for record in color_records:
        color_lookup[record["dsl"]] = {
            "idnum": record["idnum"],
            "value": record["dpg_value"],
            "kind": record["kind"],
            "dpg": record["dpg"],
            "category": record["category"],
        }

    return {
        "component": component_lookup,
        "theming": style_lookup | color_lookup,
    }


# Backwards-compatible alias while the port is in progress.
def get_lookup_table(
    metadata_path: str | Path = DEFAULT_AGGREGATOR_OUTPUT_PATH,
) -> LookupTable:
    return build_lookup_table(metadata_path)


def require_component_meta(
    component_name: str,
    lookup: LookupTable,
) -> dict[str, Any]:
    try:
        return lookup["component"][component_name]
    except KeyError as exc:
        raise InvalidComponentError(
            f"Unknown theme component {component_name!r}."
        ) from exc


def require_theme_property_meta(
    property_name: str,
    lookup: LookupTable,
) -> dict[str, Any]:
    try:
        return lookup["theming"][property_name]
    except KeyError as exc:
        raise InvalidThemingTargetError(
            f"Unknown theme property {property_name!r}."
        ) from exc



# -----------------------------------------------------------------------------
# Style value normalization
# -----------------------------------------------------------------------------


def normalize_style_value(
    property_name: str,
    raw_value: Any,
    num_args: int,
) -> dict[str, Any]:
    """Normalize a DSL style value into dpg.add_theme_style kwargs."""
    if isinstance(raw_value, set):
        raise InvalidThemeValueError(
            f"{property_name!r} cannot use a set because x/y ordering is unstable."
        )

    if isinstance(raw_value, Mapping):
        return normalize_style_mapping(property_name, raw_value, num_args)

    if isinstance(raw_value, (list, tuple)):
        return normalize_style_sequence(property_name, raw_value, num_args)

    if num_args != 1:
        raise InvalidThemeValueError(
            f"{property_name!r} expects {num_args} values, got scalar {raw_value!r}."
        )

    return {"x": raw_value}


def normalize_style_sequence(
    property_name: str,
    values: list[Any] | tuple[Any, ...],
    num_args: int,
) -> dict[str, Any]:
    if num_args not in {1, 2}:
        raise InvalidThemeValueError(
            f"{property_name!r} has unsupported num_args={num_args!r}."
        )

    if len(values) != num_args:
        raise InvalidThemeValueError(
            f"{property_name!r} expects {num_args} value(s), got {len(values)}."
        )

    if num_args == 1:
        return {"x": values[0]}

    return {"x": values[0], "y": values[1]}


def normalize_style_mapping(
    property_name: str,
    value: Mapping[str, Any],
    num_args: int,
) -> dict[str, Any]:
    if num_args == 1:
        expected_keys = {"x"}
    elif num_args == 2:
        expected_keys = {"x", "y"}
    else:
        raise InvalidThemeValueError(
            f"{property_name!r} has unsupported num_args={num_args!r}."
        )

    actual_keys = set(value)

    if actual_keys != expected_keys:
        raise InvalidThemeValueError(
            f"{property_name!r} expects keys {sorted(expected_keys)}, "
            f"got {sorted(actual_keys)}."
        )

    return {key: value[key] for key in sorted(expected_keys)}


# -----------------------------------------------------------------------------
# Theme compiler
# -----------------------------------------------------------------------------


def compile_dsl_config(
    config: Mapping[str, Any],
    lookup: LookupTable,
) -> ThemeCompileResult:
    theme_specs = extract_theme_specs(config)
    return compile_theme_specs(theme_specs, lookup)


def compile_theme_specs(
    theme_specs: Mapping[str, Any],
    lookup: LookupTable,
) -> ThemeCompileResult:
    theme_ids: dict[str, Any] = {}

    for raw_theme_name, component_specs in theme_specs.items():
        theme_name = str(raw_theme_name)

        if not isinstance(component_specs, Mapping):
            raise TypeError(
                f"Expected theme {theme_name!r} to contain component mappings."
            )

        theme_id = dpg.add_theme(
            tag=theme_name,
            user_data={},
        )

        theme_user_data: dict[str, Any] = {
            "is_global": theme_name == "$global",
            "components": {},
        }

        for raw_component_name, property_specs in component_specs.items():
            component_name = str(raw_component_name)

            if not isinstance(property_specs, Mapping):
                raise TypeError(
                    f"Expected component {component_name!r} in theme {theme_name!r} "
                    "to contain property mappings."
                )

            theme_component_id, component_user_data = compile_theme_component(
                theme_id=theme_id,
                component_name=component_name,
                property_specs=property_specs,
                lookup=lookup,
            )

            theme_user_data["components"][theme_component_id] = component_user_data

        dpg.set_item_user_data(theme_id, theme_user_data)
        theme_ids[theme_name] = theme_id

    return {
        "theme_count": len(theme_ids),
        "themes": theme_ids,
    }


def compile_theme_component(
    theme_id: Any,
    component_name: str,
    property_specs: Mapping[str, Any],
    lookup: LookupTable,
) -> tuple[Any, dict[str, Any]]:
    component_meta = require_component_meta(component_name, lookup)

    theme_component_id = dpg.add_theme_component(
        item_type=component_meta["value"],
        parent=theme_id,
    )

    property_rule_ids: dict[str, Any] = {}

    for raw_property_name, raw_value in property_specs.items():
        property_name = str(raw_property_name)

        rule_id = compile_theme_property(
            theme_component_id=theme_component_id,
            component_name=component_name,
            property_name=property_name,
            raw_value=raw_value,
            lookup=lookup,
        )

        property_rule_ids[property_name] = rule_id

    return theme_component_id, {
        "component": component_meta["dpg"],
        "properties": property_rule_ids,
    }


def compile_theme_property(
    theme_component_id: Any,
    component_name: str,
    property_name: str,
    raw_value: Any,
    lookup: LookupTable,
) -> Any:
    property_meta = require_theme_property_meta(property_name, lookup)
    property_kind = property_meta["kind"]

    if property_kind == "style":
        style_kwargs = normalize_style_value(
            property_name=property_name,
            raw_value=raw_value,
            num_args=property_meta["num_args"],
        )

        return dpg.add_theme_style(
            target=property_meta["value"],
            parent=theme_component_id,
            category=property_meta["category"],
            **style_kwargs,
        )

    if property_kind == "color":
        return dpg.add_theme_color(
            target=property_meta["value"],
            value=parse_color(raw_value),
            parent=theme_component_id,
            category=property_meta["category"],
        )

    raise InvalidThemingTargetError(
        f"Theme property {property_name!r} on component {component_name!r} "
        f"has unsupported kind {property_kind!r}."
    )


# -----------------------------------------------------------------------------
# Direct runner
# -----------------------------------------------------------------------------


def run_engine_direct(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    output_path: str | Path = DEFAULT_ENGINE_OUTPUT_PATH,
    metadata_path: str | Path = DEFAULT_AGGREGATOR_OUTPUT_PATH,
) -> ThemeCompileResult:
    dpg.create_context()
    config = load_yaml(input_path)
    lookup = build_lookup_table(metadata_path)
    result = compile_dsl_config(config, lookup)

    save_json(Path(output_path), result, indent=2)
    return result


# Temporary compatibility shim while older tests/scripts still call this name.
def load_static_test() -> ThemeCompileResult:
    config = load_yaml(DEFAULT_INPUT_PATH)
    lookup = build_lookup_table(DEFAULT_AGGREGATOR_OUTPUT_PATH)
    return compile_dsl_config(config, lookup)





































# # diesel/engine/engine.py
# """
# Direct engine test runner.

# Called from:

#     python ./diesel engine

# This file should not do work at import-time.
# Keep direct testing behind run_engine_direct().
# """

# from __future__ import annotations
# import dearpygui.dearpygui as dpg

# from builder.aggregator import get_style_num_args
# from tools import read_file, save_json, load_json

# from pathlib import Path
# from typing import Any

# import json
# import yaml

# import colorsys
# import inspect
# import re
# import os

# from config import DEFAULT_INPUT_PATH, DEFAULT_ENGINE_OUTPUT_PATH, DEFAULT_AGGREGATOR_OUTPUT_PATH

# # ENGINE_DIR = Path(__file__).resolve().parent
# # PACKAGE_DIR = ENGINE_DIR.parent
# # PROJECT_ROOT = PACKAGE_DIR.parent

# # DEFAULT_INPUT_PATH = PROJECT_ROOT / "input" / "test.yaml"
# # DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "engine.txt"

# def load_yaml(path: Path) -> dict[str, Any]:
#     raw_text = read_file(path)
#     loaded_data = yaml.safe_load(raw_text)

#     if loaded_data is None:
#         return {}

#     if not isinstance(loaded_data, dict):
#         raise TypeError(f"Expected YAML root to be a mapping, got {type(loaded_data).__name__}")

#     return loaded_data


# def extract_theme_config(config: dict[str, Any]) -> dict[Any, Any]:
#     """
#     Pull the `$themes` block out of the loaded YAML.
#     """
#     theme_specs = config.get("$themes", {})

#     if not isinstance(theme_specs, dict):
#         raise TypeError("Expected `$themes` to be a mapping.")

#     return theme_specs


# def load_dsl_config(config: dict[str, Any]) -> dict[str, Any]:
#     """
#     load DIESEL configuration.

#     This DOES build DearPyGUI themes into the context.
#     It does not currently verify that the expected structure is correct.
#     """
#     theme_specs = extract_theme_config(config)

#     themes: dict[str, Any] = {}

#     for theme_key, component_specs in theme_specs.items():
#         theme_tag = str(theme_key)

#         if not isinstance(component_specs, dict):
#             raise TypeError(
#                 f"Expected theme {theme_key!r} to contain component mappings."
#             )

#         themes[theme_tag] = {
#             "is_global": theme_key == "$global",
#             "components": {},
#         }

#         for component_name, property_specs in component_specs.items():
#             if not isinstance(property_specs, dict):
#                 raise TypeError(
#                     f"Expected component {component_name!r} in theme {theme_key!r} "
#                     "to contain property mappings."
#                 )

#             themes[theme_tag]["components"][str(component_name)] = {
#                 "property_count": len(property_specs),
#                 "properties": list(property_specs.keys()),
#             }

#     return {
#         "theme_count": len(themes),
#         "themes": themes,
#     }



# def run_engine_direct(
#     input_path: str | Path = DEFAULT_INPUT_PATH,
#     output_path: str | Path = DEFAULT_ENGINE_OUTPUT_PATH,
# ):
#     pass






# IMPORT_PATH = "/Users/greysonturner/2026_code/diesel/input/test.yaml"
# SOURCE_PATH = "/Users/greysonturner/2026_code/diesel/output/aggregator.json"
# EXPORT_PATH = "/Users/greysonturner/2026_code/diesel/output/engine.txt"


# # ---------- Parsing Helpers ----------
# def parse_color(value):
#     """Convert 'rgb()', 'rgba()', 'hsl()', 'hsla()', or packed int -> [r,g,b,a]."""
#     if isinstance(value, int):
#         r = (value >> 0) & 255
#         g = (value >> 8) & 255
#         b = (value >> 16) & 255
#         a = (value >> 24) & 255
#         return [r, g, b, a]
#     if isinstance(value, list):
#         return value + [255] if len(value) == 3 else value
#     if isinstance(value, str):
#         if value.startswith("rgb"):
#             nums = list(map(int, re.findall(r"\d+", value)))
#             return [*nums, 255] if len(nums) == 3 else nums
#         if value.startswith("hsl"):
#             nums = re.findall(r"[\d.]+", value)
#             h, s, l = float(nums[0]), float(nums[1]), float(nums[2])
#             a = float(nums[3]) if len(nums) == 4 else 1.0
#             return hsl_to_rgb(h, s, l, a)
#     return [255, 255, 255, 255]

# def hsl_to_rgb(h, s, l, a=1.0):
#     r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
#     return [int(r*255), int(g*255), int(b*255), int(a*255)]


# def build_lookup_table():
#     source_data = load_json(SOURCE_PATH)
#     dpg_members = inspect.getmembers(dpg)
    
#     dpg_component_targets = { # ZERO IS RESERVED!!!
#         "$default": { "idnum": 0, "value": 0, "dpg": "mvAll" }
#     }
#     dpg_theming_styles = {}
#     dpg_theming_colors = {}
#     for item in source_data["raws"]["item"]:
#         dpg_component_targets[ item["dsl"] ] = { 
#             "idnum":    item["idnum"], 
#             "value":    item["dpg_value"], 
#             "dpg":      item["dpg"]
#         }
#     for item in source_data["raws"]["style"]:
#         dpg_theming_styles[ item["dsl"] ] = {
#             "idnum":    item["idnum"],
#             "value":    item["dpg_value"], 
#             "kind":     item["kind"],
#             "dpg":      item["dpg"],
#             "cat":      item["category"],
#             "nargs":    item["traits"].get("num_args") or get_style_num_args(item["im_name"], item["category"], item["dpg_value"]) 
#         }
#     for item in source_data["raws"]["color"]:
#         dpg_theming_colors[ item["dsl"] ] = {
#             "idnum":    item["idnum"], 
#             "value":    item["dpg_value"], 
#             "kind":     item["kind"],
#             "dpg":      item["dpg"],
#             "cat":      item["category"]
#         }
#     dpg_theming_targets = dpg_theming_styles | dpg_theming_colors
#     return {
#         "component": dpg_component_targets,
#         "theming":  dpg_theming_targets
#     } 


# def get_lookup_table():
#     aggregate_metadata = load_json(DEFAULT_AGGREGATOR_OUTPUT_PATH)
#     component

# class InvalidComponentError(SyntaxError):
#     """ Raised when a component is unavailable. """
#     pass
# class InvalidThemingTargetError(SyntaxError):
#     """ Raised when a theming target is unavailable. """
#     pass

# def load_static_test():
#     yaml_data = yaml.safe_load(
#         read_file(fpath=IMPORT_PATH)
#     )
#     lookup_table = build_lookup_table()

#     for instruction in yaml_data:
#         match instruction:
#             case "$themes":
#                 themes = yaml_data["$themes"]
#                 theme_instances = {}
#                 # BEGIN START OF THEME CODE
#                 for (theme, components) in themes.items():
#                     is_global = (True if theme == "$global" else False)
#                     theme_object = dpg.add_theme(
#                         tag = theme,
#                         user_data = dict({})
#                     )
#                     for component, theming in components.items():
#                         if component not in lookup_table["component"]:
#                             raise InvalidComponentError(component, theming)
#                         component_data = lookup_table[component]
#                         tmp_component = dpg.add_theme_component(
#                             item_type=component_data["value"],
#                             parent=theme_object
#                         )
#                         component_children = {}
#                         for TH_target, TH_data in theming.items():
#                             if TH_target not in lookup_table["theming"]:
#                                 raise InvalidThemingTargetError(TH_target, TH_data, component)
#                             target_data = lookup_table[TH_target]
#                             tmp_theming_rule = None
#                             if target_data["kind"] == "style":
#                                 value_dict = {}
#                                 if isinstance(TH_data, (tuple, list)):
#                                     if target_data["nargs"] == 2 and (len(TH_data) >= 2):
#                                         value_dict = {
#                                             "x": TH_data[0], "y": TH_data[1]    
#                                         }
#                                     elif len(TH_data) == 1: # 1 argument only
#                                         value_dict = { "x": TH_data[0] } # Handle the list like a single value
#                                     else: 
#                                         raise IndexError("Invalid number of arguments passed!", TH_target, TH_data, component)
#                                 elif isinstance(TH_data, dict):

#                                     if target_data["nargs"] == 2 and (len(TH_data.keys()) == 2):
#                                         value_dict = {
#                                             "x": TH_data[0], "y": TH_data[1]    
#                                         }
#                                     elif target_data["nargs"] == 2:
#                                         if (len(TH_data.keys()) > 2) and (set(TH_data.keys()) in {'x','y'}):    # NOTE: This is the ONLY valid dict items you can pass!
#                                             pass
#                                         else: pass
#                                     elif len(TH_data) == 1:
#                                         value_dict = { "x": TH_data[0] } # Handle the list like a single value
#                                     else: 
#                                         raise IndexError("Invalid number of arguments passed!", TH_target, TH_data, component)
#                                 elif isinstance(TH_data, set): # A set cannot keep it's ordering for X & Y
#                                     raise TypeError(TH_target, TH_data, component)
#                                 tmp_theming_rule = dpg.add_theme_style(
#                                     target=target_data["value"],
#                                     parent=tmp_component,
#                                     category=target_data["cat"],
#                                     **value_dict

#                                 )

#                         usrdat = dict(usrdat) if (usrdat := dpg.get_item_user_data(theme_object)) is not None else {} # Enforce Type Rules
#                         usrdat[tmp_component] = {
#                             "component": component_data["dpg"],
#                             "theming": {}
#                         }
#                         dpg.set_item_user_data(theme_object, usrdat)





    







# # #from ..tools import *
# # from tools import *
# # # # Check the package name used for relative resolutions
# # # print(f"Current Package: {__package__}")

# # # # Check the physical location of this file
# # # print(f"File Directory: {os.path.dirname(os.path.abspath(__file__))}")



# # fdata = read_file(INPUT)

# # data = yaml.safe_load(fdata)
# # save_json(OUTPUT, data, indent=2)

# # # NOTE: MUST VALIDATE DATA VIA JSON_SCHEMA BEFOREHAND





# # for instruction in data.keys():
# #     if instruction[0] == "$":
# #         instruction = instruction[1:]
# #     match instruction:
# #         case "themes":
# #             theme_dict = {
# #                 identifier: {
                    
# #                 } for identifier, data in (data[instruction].items())
# #             }


# #             for theme_identifier in (data[instruction]).keys():   # identifiers
# #                 theme_dict[theme_identifier] = {
# #                     key: value for key, value in data[instruction][theme_identifier].items()
# #                 }
                
                
                
# #                 FLAG_is_global = False
# #                 if theme_identifier[0] == "$":
# #                     if theme_identifier == "$global": FLAG_is_global = True
# #                     else: print("(LOGGING_INDEV)WARNING: A $ was PREFIXED incorrectly!")
                


