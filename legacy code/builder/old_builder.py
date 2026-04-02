# diesel/modules/builder/old_builder.py # INVALID 
# ===== IMPORTS =====
import dearpygui.dearpygui as dpg
from typing import *  # type: ignore
import inspect
import uuid
import re
from tools import *
from .build_config import *

# ===== DEBUG UTILITIES (REMOVE AFTER RELEASE) =====
import rich
DEBUG = True
UI_ENABLED = False

def log(msg: str):
    """Simple debug logger (prints only if DEBUG=True)."""
    if DEBUG:
        rich.print(msg)

# ===== REGEX CONSTANTS =====
pascal_2_kebab_regex = r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])'

# ===== GENERIC UTILITIES =====
def to_kebab_case(string: str) -> str:
    """ Convert PascalCase to kebab-case (handles acronyms like OMGThisIsNeat). """
    return re.sub(pascal_2_kebab_regex, '-', string).lower()

def prefix_pattern_maker(prefixes: Union[str, Iterable[str]]) -> re.Pattern:
    """ Convert prefixes to a regex pattern. Accepts either a joined string or an iterable of strings. """
    if isinstance(prefixes, str):
        return re.compile(fr"({prefixes})[a-zA-Z]+")
    elif isinstance(prefixes, Iterable):
        if not all(isinstance(p, str) for p in prefixes):
            raise TypeError("All prefixes must be strings.", prefixes)
        return prefix_pattern_maker('|'.join(prefixes))
    raise TypeError("Expected str or Iterable[str].", prefixes)

# ===== AUTOBUILDER CONFIGURATION =====
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

# ===== GLOBAL VARIABLES =====
dpg_members = inspect.getmembers(dpg)
# >>> Tables & Lambda Lookups
tables = {
    "color": [
        {"prefix": "mvThemeCol_",       "category": 0},
        {"prefix": "mvPlotCol_",        "category": 1},
        {"prefix": "mvNodeCol_",        "category": 2}
    ],"style": [
        {"prefix": "mvStyleVar_",       "category": 0},
        {"prefix": "mvPlotStyleVar_",   "category": 1},
        {"prefix": "mvNodeStyleVar_",   "category": 2},
        {"prefix": "mvNodesStyleVar_",  "category": 2}      # spelling error has to be accounted for, an extra 's' was added on some of the names
    ]
}
color_name_conversion_table = [ # Used to make minor changes to COLOR names if they match for the KEY's lambda function, each dictionary is for a CATEGORY (CORE/PLOT/NODE), 
                                 #      changes are made by assigning the result of the KEY'S VALUE lambda function to the item name.   for NAME_LOOKUP in TABLE[CATEGORY]: if NAME_LOOKUP(kebab_name): kebab_name = TABLE[CATEGORY][LOOKUP] (kebab_name); break
    # When a match occurs, the loop breaks, so only one match and alteration may occur per input
    {   # ---- CORE CATEGORY NAME CHANGES ----
        (lambda input_name  : input_name.startswith("plot-"))   : (lambda input_name: f'color-{input_name}'),
        (lambda input_name  : True)                             : (lambda input_name: f'{input_name}-color') # DEFAULT
    },{ # ---- PLOT CATEGORY NAME CHANGES ----
        (lambda input_name  : input_name.startswith("plot-"))   : (lambda input_name: input_name),
        (lambda input_name  : True)                             : (lambda input_name: f'plot-{input_name}')  # DEFAULT
    },{ # ---- NODE CATEGORY NAME CHANGES ----
        (lambda input_name  : input_name.startswith("grid-"))   : (lambda input_name: f'node-editor-{input_name}'),
        (lambda input_name  : input_name.startswith("node-"))   : (lambda input_name: f'nodes-{input_name}'),
        (lambda input_name  : True)                             : (lambda input_name: f'node-{input_name}')  # DEFAULT
    }
]
pixel_style_lookup = ( # used by `get_style_uses_pixels()`
    ('triangle'), # Resolves an issue where 'angle' triggers a false on uses-pixels, when it does for "mvNodeStyleVar_PinTriangleSideLength"
    ('alpha', 'angle', 'align', 'segements'), # If the style string name contains any of these substrings, it is unsupported for px units
    ('marker'),  # If this is found in the string, and does not contain anything from `pixel_style_lookup[2]`, it is unsupported for px units
    ('size', 'weight')
)

# >>> >>> Autobuilder Configuration Functions
def get_style_uses_pixels(style_dss_name: str) -> bool:
    """ Returns if the DearPyGui style, in **DSS** name format (kebab-case), uses pixels in practice as an implied unit of measurement.\nSpecific to styles. """
    if contains_any(style_dss_name, pixel_style_lookup[0]): # mvNodeStyleVar_PinTriangleSideLength before ANGLE triggers as false
        return True
    if contains_any(style_dss_name, pixel_style_lookup[1]):
        return False
    if contains_any(style_dss_name, pixel_style_lookup[2]) and not contains_any(style_dss_name, pixel_style_lookup[3]):
        return False
    return True

def get_style_num_args(style_im_name: str, category: int, item_value: int) -> int:
    """ Returns for the DearPyGui style, in **IM_NAME** name format (***prefix*** removed), the number of arguments the style will use – either 1 or 2.\nSpecific to styles. """
    if category == 0: # mvStyleVar
        if contains_any(style_im_name, ("Align", "Padding", "Item", "WindowMin")):
            return 2
    elif category == 1: # mvPlotStyleVar
        if item_value > 10:
            return 2 
    return 1 # mvNode(s)StyleVar & Remaining

# >>> Autobuilder Function
def autobuilder(cache_dir=None):
    # Prefix REGEX patterns for colors and styles
    color_re_pattern, style_re_pattern = (prefix_pattern_maker([subitem['prefix'] for subitem in tables[tname]]) for tname in ('color','style'))
    build_results = {
        "styles": [],
        "colors": [],
        "widgets":[]
    }
    id_counter = UniqueCounter() 
    # XXX: STAGE__INSPECT --> Inspect the DPG Module for members and Sort them
    for item_name, item_value in dpg_members:
        # STYLE AUTOBUILDER
        if style_re_pattern.match(item_name):
            for table_row in tables[ (object_kind := "style") ]:
                if item_name.startswith(prefix := table_row["prefix"]):
                    imname_item_name = item_name.removeprefix(prefix)
                    kebab_item_name  = to_kebab_case(imname_item_name)
                    category = table_row["category"]
                    num_args = get_style_num_args(imname_item_name, category, item_value)

                    build_results["styles"].append(
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
        # COLOR AUTOBUILDER
        elif color_re_pattern.match(item_name):
            for table_row in tables[ (object_kind := "color") ]:
                if item_name.startswith(prefix := table_row["prefix"]):
                    imname_item_name = item_name.removeprefix(prefix)
                    kebab_item_name  = to_kebab_case(imname_item_name)
                    category = table_row["category"]

                    # Quick name adjustments, a name 'adjustment' WILL BE APPLIED NO MATTER WHAT, some adjustments MAKE NO REAL MODIFICATIONS
                    for key_gatekeeper, val_name_changer in color_name_conversion_table[category].items():
                        if key_gatekeeper(kebab_item_name):
                            kebab_item_name = val_name_changer(kebab_item_name)
                            break # Name has been changed once, immediatly exit loop

                    build_results["colors"].append(
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
    for style_object in build_results['styles']:
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
    for index, item in enumerate(build_results["styles"]):
        iname = item['im_name']
        target_data = dict()
        for style_item in parsed_data[item['category']]:
            if style_item['name'] == iname:
                target_data.update(style_item)
                break
        else:
            log(f"Unable to find a matching style dict to combine with `{iname}`!")
            continue
        # Assume that a "configuration" dict inside already exists for any style
        item['configuration']['value_type'] = target_data['type']
        item['configuration']['docstring'] = target_data['docstring'] 
        item['configuration']['default'] = target_data['default_value']
        build_results['styles'][index] = item
    
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

    return build_results



# FILESTORE = ".../march_code/diesel/tools/indev/tests/localstore" # BUG: STRIPPED FULL PATH!!! 
#import pyperclip


__all__ = [
    "to_kebab_case", "autobuilder", "get_style_num_args", "prefix_pattern_maker",
    "STYLE_SPECS", "VALID_TYPES", "DOCSTRING_MAPS", 
    "dpg_members", "tables", "color_name_conversion_table"

]