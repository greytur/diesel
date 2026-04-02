# diesel/modules/builder/build_config.py # INVALID
import re

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

__all__ = [
    "VALID_TYPES", "DOCSTRING_MAPS", "STYLE_SPECS"
]

# ---  DOCUMENT STATUS ---
# XXX: Properly IMP?