# diesel/builder/aggregator.py
# Aggregates everything for the builder system
# BUILT FOR: DearPyGUI Version 2.0
# ===== IMPORTS =====
from typing import *  # type: ignore
import dearpygui.dearpygui as dpg
import subprocess
import inspect
import logging
import uuid
import sys
import os
import re

# ===== LOCAL IMPORTS =====
from tools import *
from builder.naming import *
from config import AGGREGATOR_CONFIG, entity_ref_rgx
from engine.dpg_item_classifier import *

# ===== SIMPLE SETUP =====
logger              = get_logger(level=logging.INFO)
dpg_members         = inspect.getmembers(dpg)
entity_ref_pattern  = re.compile(entity_ref_rgx)

# ===== CONSTANTS =====
MODIFIER_PREFIX_DICT    = AGGREGATOR_CONFIG["modifier_prefix_dict"]
EXTERNAL_REFERENCES     = AGGREGATOR_CONFIG["external_references"]

# ===== GENERIC UTILITIES =====
def get_style_num_args(im_name: str, category: int, item_value: int) -> int:
    """ Returns the number of arguments a DearPyGUI Style will use`[1 OR 2]` """
    if category == 0: # mvStyleVar 
        if contains_any(im_name, ("Align", "Padding", "Item", "WindowMin")):
            return 2
    elif category == 1: # mvPlotStyleVar
        if item_value > 10:
            return 2 
    return 1 # mvNode(s)StyleVar & Remaining

# # >>> Aggregator Functions
# def resolve_dpg_item(name):
#     for prefix, (kind, category) in MODIFIER_PREFIX_DICT.items():
#         if name.startswith(prefix):
#             im_name = name.removeprefix(prefix)         #kebab_name = to_kebab_case(im_name)
#             return kind, category, im_name              #, kebab_name
#     return None

def build_item_record(
        kind: str, dpg_name: str, dsl_name:str, im_name: str,
        item_value: int, category: int, 
        id_counter: UniqueCounter
    ):
    """ Builds a record for a DPG item. """
    return {
        "kind":         kind,
        "dpg":          dpg_name,
        "dsl":          dsl_name,
        "im_name":      im_name,
        "idnum":        id_counter.get_next(),
        "category":     category,
        "dpg_value":    item_value,
        "meta": {
            "value_type":   None,
            "docstring":    None,
            "default":      None
        },
        "traits": { }
    }

def collect_dpg_theming_items(dpg_members: Any, id_counter: UniqueCounter):
    dpg_items = { "style": [], "color": [] }
    for dpg_name, value in dpg_members:
        # Resolve the information from the name
        result = resolve_dpg_item(name=dpg_name)
        if not result:
            continue
        kind, category, im_name = result                #, kebab_name
        # Get the DSL Name
        dsl_name = apply_naming_rules(im_name, kind, category)
        # Build raw item record
        raw_record = build_item_record(
            kind=kind,
            dpg_name=dpg_name,
            dsl_name=dsl_name,
            im_name=im_name,
            item_value=value,
            category=category,
            id_counter=id_counter
        )
        dpg_items[kind].append(raw_record)
    return dpg_items

def collect_external_refs(external_refs, cache_dir=None) -> dict:
    """ Collects external references from a cache directory or using the URLs from `external_refs` """
    collected_refs = {}
    is_cache_stable = True if (isinstance(cache_dir, str)) else False  # Used to toggle caching, mainly from NotADirectoryError and FileNotFoundError

    for ref in external_refs:
        urls_docket = [ref["primary_url"]] + ref.get("backup_urls", [])  # The primary url followed by any backups
        ref_fetch_success = False

        for current_url in urls_docket:
            try:
                result = fetch_url(
                    url       = current_url,
                    filename  = ref["save_as"],
                    use_cache = ref["docache"] and is_cache_stable,  # Will try to get from the cache first before using any networking
                    cache_dir = cache_dir,
                )

            except (FileNotFoundError, NotADirectoryError) as e:
                if isinstance(e, FileNotFoundError) and e.filename == "curl":
                    logger.exception("The command `curl` was not found when called via subprocess!")
                    raise # EXIT

                logger.exception(
                    "Cache path '%s' is unusable/unstable (missing or not a directory); "
                    "retrying this URL without caching (continuing to next url if fetch fails).",
                    cache_dir,
                )
                is_cache_stable = False  # Disable the cache for this run
                logger.warning(
                    "Caching within collect_external_refs has been disabled for this run! "
                    "(future calls to the function are not affected, only fetch_url calls within this run)")
                
                
                try:
                    result = fetch_url(url=current_url, use_cache=False)
                except (NoInternetConnectionError, FileNotFoundError, OSError):
                    logger.exception("Failed to fetch URL and got an exception/error that prevents continuation "
                        "(cache-retry failed).")
                    raise
                except (ValueError, subprocess.CalledProcessError, InvalidURLError):
                    logger.exception("Failed to fetch URL on retry; ignoring and continuing to next url (url='%s')",current_url)
                    continue
                except Exception:
                    logger.exception("Unknown error occurred while retrying URL: %s", current_url)
                    raise
                else:
                    collected_refs[ref["refname"]] = result
                    ref_fetch_success = True
                    logger.info("Successfully fetched reference '%s' from the URL: '%s'", ref["refname"], current_url)
                    break

            except NoInternetConnectionError:
                logger.exception("No internet connection; cannot fetch URL.")
                raise
            except OSError:
                logger.exception("Subprocess failed to run curl; likely a permissions/resource issue.")
                raise
            except (InvalidURLError, ValueError, subprocess.CalledProcessError):
                logger.exception("Failed to fetch URL: %s", current_url)  # In order: invalid Url, fetch returned no content, subprocess.run exit code was not 0
                continue  # try next backup URL
            except Exception:
                logger.exception("Unknown error occurred while fetching URL: %s", current_url)
                raise

            else:
                collected_refs[ref["refname"]] = result
                ref_fetch_success = True

                if not cache_dir:  # If there was no caching involved, we know it was fetched from ONLINE not the cache
                    logger.info("Successfully fetched reference '%s' from the URL: '%s'", ref["refname"], current_url)
                else:  # We fetched the reference
                    logger.info("Successfully fetched reference '%s'", ref["refname"])

                break  # stop trying backups

        if not ref_fetch_success:
            if ref.get("require", False):
                logger.error("Required reference '%s' could not be fetched from any URL.", ref["refname"])
                raise RuntimeError(f"Required reference '{ref['refname']}' failed to fetch.")

            elif ref.get("desired", False):
                logger.warning("Desired reference '%s' could not be fetched from any URL. Skipping.", ref["refname"])

            else:
                logger.info("Optional reference '%s' could not be fetched. Skipping silently.", ref["refname"])

    return collected_refs


def collect_dpg_items(dpg_members: Any, id_counter: UniqueCounter, external_references: Any):
    pattern = re.compile(r"X\(\s*(mv[a-zA-Z0-9]+)\s*\)")
    item_types = pattern.findall(external_references["mvAppItemTypes.inc"])
    
    dpg_items = { "entity": [] }
    for item_index, item in enumerate(item_types):
        kind = "entity"
        im_name = item.removeprefix('mv')
        category = 0
        dsl_name = apply_naming_rules(im_name, kind, category)
        raw_record = build_item_record(
            kind="entity",
            dpg_name=item,
            im_name=im_name,
            dsl_name=dsl_name,
            item_value=(item_index + 1),
            category=category,
            id_counter=id_counter
        )
        dpg_items[kind].append(raw_record)
    return dpg_items


def apply_naming_rules(name, scope, category):
    # Handle any preprocessing required (all naming information is passed by default)
    name = PREPROCESSOR_FUNCTION(name, scope, category) 
    for rule in NAME_RULES[scope][category]: # Locate valid rules
        if rule.when(name):                 # If NameRule can be applied, do so.
            return rule.then(name)          # Get the NameRule-compliant name
    return name                             # No "DEFAULT" NameRule was active
   
     
# >>> Aggregator Function
def aggregate(cache_dir=None):
    # Aggregation Setup
    counter = UniqueCounter()
    counter.get_next()          # BUG: USED To allow mvAll to properly be slotted into place at idnum `0`
    #dpg_members = inspect.getmembers(dpg)

    raw_theming_items = collect_dpg_theming_items(dpg_members, id_counter=counter)
    external_references = collect_external_refs(EXTERNAL_REFERENCES, cache_dir=cache_dir)
    raw_target_items = collect_dpg_items(dpg_members, id_counter=counter, external_references=external_references)

    return {
        "raws": raw_theming_items | raw_target_items, # type: ignore
        #"refs": external_references,
    }



def collect_dpg_theming_items2(dpg_members: Any, id_counter: UniqueCounter):
    dpg_items = { "style": [], "color": [] }
    for dpg_name, value in dpg_members:
        # Resolve the information from the name
        result = resolve_dpg_item(name=dpg_name)
        if not result:
            continue
        kind, category, im_name = result                #, kebab_name
        # Get the DSL Name
        dsl_name = apply_naming_rules(im_name, kind, category)
        # Build raw item record
        raw_record = build_item_record(
            kind=kind,
            dpg_name=dpg_name,
            dsl_name=dsl_name,
            im_name=im_name,
            item_value=value,
            category=category,
            id_counter=id_counter
        )
        dpg_items[kind].append(raw_record)


    pattern = re.compile(r"X\(\s*(mv[a-zA-Z0-9]+)\s*\)")
    item_types = pattern.findall(EXTERNAL_REFERENCES["mvAppItemTypes.inc"])
    
    dpg_items = { "item": [] }
    for item_index, item in enumerate(item_types):
        kind = "item"
        im_name = item.removeprefix('mv')
        category = 0
        dsl_name = apply_naming_rules(im_name, kind, category)
        raw_record = build_item_record(
            kind="item",
            dpg_name=item,
            im_name=im_name,
            dsl_name=dsl_name,
            item_value=(item_index + 1),
            category=category,
            id_counter=id_counter
        )
        dpg_items[kind].append(raw_record)
    return dpg_items
    return dpg_items


# >>> Aggregator Functions
def resolve_dpg_item(name):
    for prefix, (kind, category) in MODIFIER_PREFIX_DICT.items():
        if name.startswith(prefix):
            im_name = name.removeprefix(prefix)         #kebab_name = to_kebab_case(im_name)
            return kind, category, im_name              #, kebab_name
    return None

modifier_prefix_dict = {
        # PREFIX            # KIND   # CATEGORY
        "mvStyleVar_":      ("style", 0),
        "mvPlotStyleVar_":  ("style", 1),
        "mvNodeStyleVar_":  ("style", 2),
        "mvNodesStyleVar_": ("style", 2),
        "mvThemeCol_":      ("color", 0),
        "mvPlotCol_":       ("color", 1),
        "mvNodeCol_":       ("color", 2),
        "mvNodesCol_":      ("color", 2),
    }

def collect_member_records(members: list[tuple[str, Any]], counter: UniqueCounter, references: dict):
    
    
    members_dict = {k: v for (k, v) in members}
    modifier_prefix_dict = {
        # PREFIX            # KIND   # CATEGORY
        "mvStyleVar_":      ("style", 0),
        "mvPlotStyleVar_":  ("style", 1),
        "mvNodeStyleVar_":  ("style", 2),
        "mvNodesStyleVar_": ("style", 2),
        "mvThemeCol_":      ("color", 0),
        "mvPlotCol_":       ("color", 1),
        "mvNodeCol_":       ("color", 2),
        "mvNodesCol_":      ("color", 2),
    }

    # Extract mvAppItemType names from mvAppItemTypes.inc-style source.
    entity_names = entity_ref_pattern.findall(references["mvAppItemTypes.inc"])
    
    records = {
        "modifier": {
            "style": [], "color": [],
        },
        "entity": {
            "handler": [], "registry": [],
            "value":   [], "asset":    [],
            "theming": [], "element":  [],
            "special": []
        }
    }
    
    for name, value in members:
        for prefix, (domain, category) in modifier_prefix_dict.items():
            if name.startswith(prefix):
                kind     = "modifier"
                im_name  = name.removeprefix(prefix)
                dsl_name = apply_naming_rules(im_name, domain, category)
                records[kind][domain].append({
                    "kind":         kind,
                    "domain":       domain,
                    "dpg":          name,
                    "dsl":          dsl_name,
                    "im_name":      im_name,
                    "idnum":        counter.get_next(),
                    "category":     category,
                    "dpg_value":    value,
                    
                })



def aggregator(cache_dir=None):
    # Basic Aggregation Setup
    id_counter   = UniqueCounter(start=1)     # NOTE: Skips 0 because it is reserved for mvAll
    references = collect_external_refs(
        external_refs=EXTERNAL_REFERENCES, 
        cache_dir=cache_dir
    )

    member_records = collect_member_records(
        members=dpg_members, 
        counter=id_counter,
        references=references
    )

    modifiers = {
        "styles": [], "colors": [],
    }
    entities = {
        "handler": [], "registry": [],
        "value":   [], "asset":    [],
        "theming": [], "element":  [],
        "special": []
    }






# def compose_member_record(
#         kind: str, item_name: str, dsl_name:str, im_name: str,
#         item_value: int, category: int, 
#         id_counter: UniqueCounter
#     ):
#     """ Builds a record for a DPG item. """
#     return {
#         "kind":         "entity"|"modifier",
#         "domain":       domain,
#         "dpg":          item_name,
#         "dsl":          dsl_name,
#         "im_name":      im_name,
#         "idnum":        id_counter.get_next(),
#         "category":     category,
#         "dpg_value":    item_value,
#         "meta": {
#             "docstring":    None,   # ALL
#         },
#         "traits": { 
#             "value_type":   None, # If style
#             "default":      None, # If color/style
#             "dimension":    None, # If entity
#             "source":       None, # If entity
#             "role":         None, # If entity 
#         }
#     }

















STYLE_SPECS = [
    {
        "name": "imgui",
        "category": 0,
        "url": "https://raw.githubusercontent.com/ocornut/imgui/refs/heads/docking/imgui.cpp",
        "snip_start": "ImGuiStyle::ImGuiStyle()",
        "snip_end": "// Behaviors",
        "regex": re.compile(r'\s+([A-Z][a-zA-Z]+)\s+=\s+(.*?);\s*//\s*(.*)'),
        "name_pos": 0, "type_pos": 1, "doc_pos": 2, "default_pos": 1, 
        "do_manual_docstring": False,
        "merge_function": None
        #^[ \t]+([A-Z][a-zA-Z]+)[ \t]+=[ \t]+(.*?);[ \t]*//[ \t]*(.*)$
    },
    {
        "name": "implot_1",
        "category": 1,
        "url": "https://raw.githubusercontent.com/epezent/implot/f156599faefe316f7dd20fe6c783bf87c8bb6fd9/implot.h",
        "snip_start": "enum ImPlotStyleVar_ {",
        "snip_end": "ImPlotStyleVar_COUNT",
        "regex": re.compile(r'\s+(?:.*?_)([A-Z][a-zA-Z]+),\s+//\s(.*?),\s+(.*?)(?:\n|$)'),
        "name_pos": 0, "type_pos": -1, "doc_pos": 1, "default_pos": -1,
        "do_manual_docstring": False,
        "merge_function": None
        #\s+(?:.*?_)([A-Z][a-zA-Z]+),\s+//\s([a-zA-Z0-9]*?),\s+(.*?)(?:\n|$)
    },
    {
        "name": "implot_2",
        "category": 1,
        "url": "https://raw.githubusercontent.com/epezent/implot/f156599faefe316f7dd20fe6c783bf87c8bb6fd9/implot.h",
        "snip_start": "struct ImPlotStyle {",
        "snip_end": "// style colors",
        "regex": re.compile(r'\s+(.*?)\s+([A-Z][a-zA-Z]+);\s+//\s=\s+(.*?),?\s+(.*?)(?:\n|$)'),
        "name_pos": 1, "type_pos": 0, "doc_pos": 3, "default_pos": 2,
        "do_manual_docstring": False,
        "merge_function": (
            lambda origin_dict, spec_dict: {
            "name": origin_dict["name"], "type": origin_dict["type"],
            "docstring": origin_dict["docstring"] if len(origin_dict["docstring"]) >= len(spec_dict["docstring"]) else spec_dict["docstring"],
            "default_value": spec_dict["default_value"] if not origin_dict["default_value"] else origin_dict["default_value"]
        } if origin_dict["name"] == spec_dict["name"] else origin_dict
        )
        #^\s+([ac-zAC-Z0-9]*?)\s+([A-Z][a-zA-Z]+);\s+//\s=\s+(.*?),?\s+(.*?)(?:\n|$)
    },
    {
        "name": "imnode",
        "category": 2,
        "url": "https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/thirdparty/imnodes/imnodes.cpp",
        "snip_start": "ImNodesStyle::ImNodesStyle()",
        "snip_end": "Colors()",
        "regex": re.compile(r'([A-Z][a-zA-Z]+)\(([0-9].*?)\),'),
        "name_pos": 0, "type_pos": 1, "doc_pos": -1, "default_pos": 1,
        "do_manual_docstring": True,
        "merge_function": None
        #([A-Z][a-zA-Z]+)\(([0-9].*?)\),
    }
]
VALID_TYPES = ["tuple[float, float]", "float", "int"]
DOCSTRING_MAPS = [
    {},
    {},
    { # Node Grouping
        "Grid": { 
            "Spacing": "The spacing between the grid lines of the NodeEditor background canvas.", # GridSpacing
        },
        "Link": {
            "Hover": "The distance from a link line that the cursor must be (in pixels) to trigger a hovering event.", # LinkHoverDistance
            "Line": "The amount of line segments that a link should have between two node pins.", # LinkLineSegmentsPerLength
            "Thickness": "The fixed pixel thickness that a link line will render as in the NodeEditor.", # LinkThickness
        },
        "Node": {
            "Padding": "The padding (in pixels) that the contents of the Node widget will have.", # NodePadding
            "Corner": "The amount of pixels that will be rounded off of the edge of the Node widget's content box.", # NodeCornerRounding
            "Border": "The thickness of the border line surrounding the Node widget (in pixels).", # NodeBorderThickness
        },
        "Pin": {
            "Triangle": "The length that each side of the triangle pin will be.", # PinTriangleSideLength
            "Circle": "The radius that the circle pin will be.", # PinCircleRadius
            "Quad": "The length that each side of the quad (square) pin will be.", # PinQuadSideLength
            "Hover": "The radius from a pin that the cursor must be to trigger a hovering event.", # PinHoverRadius
            "Offset": "The number of pixels that a pin will be offset from the edge of the Node widget.", # PinOffset
            "Line": "WARNING: DOES NOT APPEAR TO WORK. The thickness of the pin-shape line when the pin shape is not 'filled'.", # PinLineThickness
        },
        "Mini": {
            "Padding": "MiniMap padding size between MiniMap Content & MiniMap Edge.", # MiniMapPadding
            "Offset": "MiniMap offset from the screen side in pixels.", # MiniMapOffset
        },
    },
]

















from legacy import prefix_pattern_maker, get_style_uses_pixels, tables, color_name_conversion_table
# >>> Auto Aggregator Function (LEGACY)
def auto_aggregate(cache_dir=None):
    # Prefix REGEX patterns for colors and styles
    color_re_pattern, style_re_pattern = (prefix_pattern_maker([subitem['prefix'] for subitem in tables[tname]]) for tname in ('color','style'))
    results = {
        "styles": [],
        "colors": [],
        "widgets":[]
    }
    id_counter = UniqueCounter() 
    # XXX: STAGE__INSPECT --> Inspect the DPG Module for members and Sort them
    for item_name, item_value in dpg_members:
        # STYLE
        if style_re_pattern.match(item_name):
            for table_row in tables[ (object_kind := "style") ]:
                if item_name.startswith(prefix := table_row["prefix"]):
                    imname_item_name = item_name.removeprefix(prefix)
                    kebab_item_name  = pascal_to_kebab_case(imname_item_name)
                    category = table_row["category"]
                    num_args = get_style_num_args(imname_item_name, category, item_value)

                    results["styles"].append(
                        {
                            "kind":         object_kind, # What kind of object is it? 
                            "dpg":          item_name,   # What is the DPG-assigned name of the item?
                            "dss":          kebab_item_name,
                            "im_name":      imname_item_name,
                            "idtag":        uuid.uuid4().hex,
                            "idnum":        id_counter.get_next(),
                            "category":     category,
                            "py_value":     item_value,
                            "configuration": {
                                "num_args":     num_args,
                                "uses_pixels":  get_style_uses_pixels(kebab_item_name)
                            }
                        }
                    )
        # COLOR 
        elif color_re_pattern.match(item_name):
            for table_row in tables[ (object_kind := "color") ]:
                if item_name.startswith(prefix := table_row["prefix"]):
                    imname_item_name = item_name.removeprefix(prefix)
                    kebab_item_name  = pascal_to_kebab_case(imname_item_name)
                    category = table_row["category"]

                    # Quick name adjustments, a name 'adjustment' WILL BE APPLIED NO MATTER WHAT, some adjustments MAKE NO REAL MODIFICATIONS
                    for key_gatekeeper, val_name_changer in color_name_conversion_table[category].items():
                        if key_gatekeeper(kebab_item_name):
                            kebab_item_name = val_name_changer(kebab_item_name)
                            break # Name has been changed once, immediatly exit loop

                    results["colors"].append(
                        {
                            "kind":         object_kind,
                            "dpg":          item_name,
                            "dss":          kebab_item_name,
                            "im_name":      imname_item_name,
                            "idtag":        uuid.uuid4().hex,
                            "idnum":        id_counter.get_next(),
                            "category":     category,
                            "py_value":     item_value,
                        }
                    )

    # Advanced Information Steps – Things like docstrings, default values, and constraints!
    # ======= PARSING SETUP CODE =======
    all_style_imnames = [set({}), set({}), set({})]
    for style_object in results['styles']:
        all_style_imnames[style_object['category']].add(style_object['im_name'])
    # ======= IMGUI DATA PARSING =======
    valid_imnames = all_style_imnames
    
    def get_snippet_str(spec):
        raw = fetch_url(url=spec["url"], cache_dir=cache_dir)
        snippet = raw.split(spec["snip_start"])[1].split(spec["snip_end"])[0]
        return snippet

    def infer_type(val):
        if "ImVec2" in val or "," in val: return VALID_TYPES[0]
        if "int" in val: return VALID_TYPES[2]
        return VALID_TYPES[1]

    def clean_default(val):
        # NOTE: THIS SECTION INCLUDES HARDCODED REPLACEMENTS FOR "MONKEY WRENCH" INPUTS --> (`IM_PI` && `ImPlotMarkerNone`)
        if val is None: return val
        val = '0.61' if 'IM_PI' in val else ('-1' if 'ImPlotMarker_None' in val else val)
        val = val.replace(".f", ".0f").replace("f", "").strip()
        val = remove_substrings(val, {'ImVec2','(',')'})
        return None if val == "" else val

    def parse_default(val, typ):
        if val is None: 
            return None
        if ',' in val or typ == VALID_TYPES[0]: 
            return tuple(float(x.strip()) for x in val.split(','))
        if typ == VALID_TYPES[1]: 
            return float(val)
        if typ == VALID_TYPES[2]: 
            return int(val)
        raise ValueError(f"Unknown default value type: {typ}")
    
    def get_docstring(name: str) -> str: # Only supports IMNODE
        for grouping, patterns in DOCSTRING_MAPS[2].items():
            if grouping in name: # is the primary grouping in the name
                for keyword, doc in patterns.items():
                    if keyword and keyword in name:  # is a grouping's sub-keyword in a name
                        return doc
        raise NotImplementedError(f"The style '{name}' is not currently supported.")

    parsed_data = [[], [], []]

    for spec in STYLE_SPECS:
        snippet = get_snippet_str(spec)
        matches = spec["regex"].findall(snippet)

        dataset = []
        for match in matches:
            name = match[spec["name_pos"]]
            if name not in valid_imnames[spec["category"]]: 
                continue
            raw_type    = match[spec["type_pos"]] if spec["type_pos"] >= 0 else ""
            raw_default = match[spec["default_pos"]] if spec["default_pos"] >= 0 else None
            doc         = match[spec["doc_pos"]] if spec["doc_pos"] >= 0 else ""

            dataset.append({
                "name": name,
                "type": infer_type(raw_type),
                "docstring": capitalize_first_letter(doc) if len(doc) else (get_docstring(name) if spec["do_manual_docstring"] else doc),
                "default_value": parse_default(clean_default(raw_default), infer_type(raw_type))
            })
        if len(parsed_data[spec["category"]]) > 0: 
            if (merge_function := spec["merge_function"]) is not None:
                # NOTE: THE MERGING DATA MUST BE THE SAME LENGTH AND ALIGN PROPERLY BASED ON POSITION, OTHERWISE MISMATCH COULD OCCUR!!!
                merged_data = []
                for (origin_data, new_data) in zip(parsed_data[spec["category"]], dataset):
                    merged_data.append(merge_function(origin_data, new_data))
                parsed_data[spec["category"]] = merged_data
            else:
                raise RuntimeError("Cannot merge categories if a merge function is not provided!")
        else:
            parsed_data[spec["category"]].extend(dataset)
    
    # ======= UPDATING BUILD RESULTS =======
    # parsed_data = [imgui_parsed_data, implot_parsed_data, imnode_parsed_data]
    for index, item in enumerate(results["styles"]):
        iname = item['im_name']
        target_data = dict()
        for style_item in parsed_data[item['category']]:
            if style_item['name'] == iname:
                target_data.update(style_item)
                break
        else:
            print(f"Unable to find a matching style dict to combine with `{iname}`!")
            continue
        # Assume that a "configuration" dict inside already exists for any style
        item['configuration']['value_type'] = target_data['type']
        item['configuration']['docstring'] = target_data['docstring'] 
        item['configuration']['default'] = target_data['default_value']
        results['styles'][index] = item
    
    # === Widget Parsing ===
    # def get_documents()
    # widget_urls = {
    #     "mvAppItemTypes.inc":"https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/src/mvAppItemTypes.inc",
    # }
    
    # tmp_text = fetch_url(url=widget_urls["mvAppItemTypes.inc"], cache_dir=local_src)
    # pattern = re.compile(
    #     r"X\(\s*(mv[a-zA-Z0-9]+)\s*\)"
    # )
    # item_types = pattern.findall(tmp_text)
    # for index, item in enumerate(item_types):
    #     x={
    #         "kind": "widget",
    #         "dpg": item,
    #         "dss": to_kebab_case(item.removeprefix("mv")),
    #         "im_name": item.removeprefix("mv"),
    #         "idtag": uuid.uuid4().hex,
    #         "idnum": GLOBAL_COUNTER.get_next(),
    #         "category": 0,
    #         "py_value": index,
    #         "configuration": {
    #             "value_type": "float",
    #             "docstring": "The spacing between the grid lines of the NodeEditor background canvas.",
    #             "default": 24.0,
    #         }
    #     }

    return results



__all__ = [
    "aggregate", "get_style_num_args",
    "STYLE_SPECS", "VALID_TYPES", "DOCSTRING_MAPS", 
    "dpg_members",

]

# ---  DOCUMENT STATUS ---
# XXX: In Development
# XXX: Modified 4/3/26 - Cleanup