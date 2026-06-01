# diesel/config.py

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

DEFAULT_CACHE_DIR = PROJECT_ROOT / "cache"
DEFAULT_INPUT_DIR = PROJECT_ROOT / "input"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

DEFAULT_INPUT_PATH = DEFAULT_INPUT_DIR / "test.yaml"
DEFAULT_AGGREGATOR_OUTPUT_PATH = DEFAULT_OUTPUT_DIR / "aggregator.json"
DEFAULT_ENGINE_OUTPUT_PATH = DEFAULT_OUTPUT_DIR / "engine.txt"






# >>> Aggregator Config

AGGREGATOR_CONFIG = {
    "modifier_prefix_dict": {
        # PREFIX            # KIND   # CATEGORY
        "mvStyleVar_":      ("style", 0),
        "mvPlotStyleVar_":  ("style", 1),
        "mvNodeStyleVar_":  ("style", 2),
        "mvNodesStyleVar_": ("style", 2),
        "mvThemeCol_":      ("color", 0),
        "mvPlotCol_":       ("color", 1),
        "mvNodeCol_":       ("color", 2),
        "mvNodesCol_":      ("color", 2),
    },   
    "external_references": [
        {
            "refname": "implot.h",   
            "require": False,            
            "desired": True,            
            "docache": True, 
            "save_as": "implot.h",
            "description": "No description given.",
            "primary_url": "https://raw.githubusercontent.com/epezent/implot/f156599faefe316f7dd20fe6c783bf87c8bb6fd9/implot.h",
            "backup_urls": [
                "https://raw.githubusercontent.com/epezent/implot/refs/heads/master/implot.h"
            ]
        },{
            "refname": "imnodes.cpp",   # The reference name, this is the [KEY] that will hold the returned str content, NOT the file.
            "require": False,           # Is this REQUIRED for functionality? Or can the step be skipped for a less desirable result?
            "desired": True,            # Is this DESIRED for functionality? Or can the step be skipped for a similar quality result?
            "docache": True,            # Does the download need to be stored locally in the cache?(Disable if changes are frequent!)
            "save_as": "imnodes.cpp",
            "description": "No description given.",
            "primary_url": "https://raw.githubusercontent.com/hoffstadt/DearPyGui/40355739b7b1be4b063b2cfc919efbdcc124fb64/thirdparty/imnodes/imnodes.cpp",
            "backup_urls": [
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/thirdparty/imnodes/imnodes.cpp", 
                "https://raw.githubusercontent.com/Nelarius/imnodes/8563e1655bd9bb1f249e6552cc6274d506ee788b/imnodes.cpp",
                "https://raw.githubusercontent.com/Nelarius/imnodes/b2ec254ce576ac3d42dfb7aef61deadbff8e7211/imnodes.cpp",
                "https://raw.githubusercontent.com/Nelarius/imnodes/refs/heads/master/imnodes.cpp"
            ]
        },{
            "refname": "imgui.cpp",
            "require": False,
            "desired": True,
            "docache": True,
            "save_as": "imgui.cpp",
            "description": "The primary C++ file of the master branch of ImGui, despite supporting docking, DearPyGui does not use the docking branch.",
            "primary_url": "https://raw.githubusercontent.com/ocornut/imgui/139e99ca37a3e127c87690202faec005cd892d36/imgui.cpp",
            "backup_urls": [
                "https://raw.githubusercontent.com/ocornut/imgui/refs/heads/docking/imgui.cpp",
            ]
        },{
            "refname": "mvAppItemTypes.inc",   
            "require": True,            
            "desired": True,
            "docache": True, 
            "save_as": "mvAppItemTypes.inc",
            "description": "Contains the AppItem types in an unrefined format, it is highly important for determining elements and widgets.",
            "primary_url": "https://raw.githubusercontent.com/hoffstadt/DearPyGui/8369d7c37b470e816405bd411e54992eeece4e60/src/mvAppItemTypes.inc",
            "backup_urls": [
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/40355739b7b1be4b063b2cfc919efbdcc124fb64/src/mvAppItemTypes.inc",
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/src/mvAppItemTypes.inc"
            ]
         },{
            "refname": "mvAppItem.h",   
            "require": True,            
            "desired": True,
            "docache": True, 
            "save_as": "mvAppItem.h",
            "description": "Contains the AppItem base class header.",
            "primary_url": "https://raw.githubusercontent.com/hoffstadt/DearPyGui/8369d7c37b470e816405bd411e54992eeece4e60/src/mvAppItem.h",
            "backup_urls": [
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/40355739b7b1be4b063b2cfc919efbdcc124fb64/src/mvAppItem.h",
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/src/mvAppItem.h"
            ]
        },{
            "refname": "mvAppItem.cpp",   
            "require": True,            
            "desired": True,
            "docache": True, 
            "save_as": "mvAppItem.cpp",
            "description": "Contains the AppItem base class code.",
            "primary_url": "https://raw.githubusercontent.com/hoffstadt/DearPyGui/8369d7c37b470e816405bd411e54992eeece4e60/src/mvAppItem.cpp",
            "backup_urls": [
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/40355739b7b1be4b063b2cfc919efbdcc124fb64/src/mvAppItem.cpp",
                "https://raw.githubusercontent.com/hoffstadt/DearPyGui/refs/heads/master/src/mvAppItem.cpp"
            ]
        },
    ]
}

item_funcs_rgx = r"[ \t]*case[ \t]+mvAppItemType::([a-zA-Z0-9]+):[ \t]*return[ \t]+\"([a-zA-Z0-9_]+)\";?"
entity_ref_rgx = r"X\(\s*(mv[a-zA-Z0-9]+)\s*\)"   # Used to extract the names from `mvAppItemType.inc`
