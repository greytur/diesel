from typing import Union, Iterable
from tools import contains_any
import re
def prefix_pattern_maker(prefixes: Union[str, Iterable[str]]) -> re.Pattern:
    """ Convert prefixes to a regex pattern. Accepts either a joined string or an iterable of strings. """
    if isinstance(prefixes, str):
        return re.compile(fr"({prefixes})[a-zA-Z]+")
    elif isinstance(prefixes, Iterable):
        if not all(isinstance(p, str) for p in prefixes):
            raise TypeError("All prefixes must be strings.", prefixes)
        return prefix_pattern_maker('|'.join(prefixes))
    raise TypeError("Expected str or Iterable[str].", prefixes)


# TODO: REMOVE SOON
def convert_color_name(name: str, category: int) -> str:
    """
    category: 0 = CORE, 1 = PLOT, 2 = NODE
    """
    if category == 0:  # CORE
        # If it starts with 'plot-', prefix with 'color-'; else suffix '-color'
        if name.startswith("plot-"):
            return re.sub(r'^plot-', 'color-', name)
        return re.sub(r'$', '-color', name)
    
    elif category == 1:  # PLOT
        # If it starts with 'plot-', leave it; else prefix with 'plot-'
        if name.startswith("plot-"):
            return name
        return re.sub(r'^', 'plot-', name)
    
    elif category == 2:  # NODE
        # 'grid-*' → 'node-editor-*', 'node-*' → 'nodes-*', else → 'node-*'
        if name.startswith("grid-"):
            return re.sub(r'^grid-', 'node-editor-', name)
        elif name.startswith("node-"):
            return re.sub(r'^node-', 'nodes-', name)
        else:
            return re.sub(r'^', 'node-', name)
    
    else:
        raise ValueError("Invalid category")
    

pixel_style_lookup = ( # used by `get_style_uses_pixels()`
    ('triangle'), # Resolves an issue where 'angle' triggers a false on uses-pixels, when it does for "mvNodeStyleVar_PinTriangleSideLength"
    ('alpha', 'angle', 'align', 'segements'), # If the style string name contains any of these substrings, it is unsupported for px units
    ('marker'),  # If this is found in the string, and does not contain anything from `pixel_style_lookup[2]`, it is unsupported for px units
    ('size', 'weight')
)

# >>> >>> Auto-Aggregator Configuration Functions
def get_style_uses_pixels(style_dss_name: str) -> bool:
    """ Returns if the DearPyGui style, in **DSS** name format (kebab-case), uses pixels in practice as an implied unit of measurement.\nSpecific to styles. """
    if contains_any(style_dss_name, pixel_style_lookup[0]): # mvNodeStyleVar_PinTriangleSideLength before ANGLE triggers as false
        return True
    if contains_any(style_dss_name, pixel_style_lookup[1]):
        return False
    if contains_any(style_dss_name, pixel_style_lookup[2]) and not contains_any(style_dss_name, pixel_style_lookup[3]):
        return False
    return True


tables = {
    "color": [
        {"prefix": "mvThemeCol_",       "category": 0},
        {"prefix": "mvPlotCol_",        "category": 1},
        {"prefix": "mvNodeCol_",        "category": 2},
        {"prefix": "mvNodesCol_",       "category": 2}      # spelling error has to be accounted for, an extra 's' was added on some of the names
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





########################## dpg_item_classifer.py

PLOT_CATEGORY_ITEMS: frozenset[str] = frozenset(
    {
        "mvPlot",
        "mvSimplePlot",
        "mvSubPlots",
        "mvPlotLegend",
        "mvPlotAxis",
        "mvAnnotation",
        "mvAxisTag",
        "mvDragPoint",
        "mvDragLine",
        "mvDragRect",
        "mvLineSeries",
        "mvScatterSeries",
        "mvStemSeries",
        "mvStairSeries",
        "mvBarSeries",
        "mvBarGroupSeries",
        "mvErrorSeries",
        "mvInfLineSeries",
        "mvHeatSeries",
        "mvImageSeries",
        "mvPieSeries",
        "mvShadeSeries",
        "mvLabelSeries",
        "mvHistogramSeries",
        "mvDigitalSeries",
        "mv2dHistogramSeries",
        "mvCandleSeries",
        "mvAreaSeries",
        "mvCustomSeries",
        "mvColorMapScale",
        "mvColorMap",
        "mvColorMapRegistry",
        "mvColorMapButton",
        "mvColorMapSlider",
    }
)


NODE_CATEGORY_ITEMS: frozenset[str] = frozenset(
    {
        "mvNodeEditor",
        "mvNode",
        "mvNodeAttribute",
        "mvNodeLink",
    }
)
