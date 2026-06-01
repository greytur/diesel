# diesel/builder/naming.py
# Handles naming rules for `aggregator.py`

import re
from typing import Callable, Iterable
from dataclasses import dataclass

CAT_CORE = 0 # dpg.mvThemeCat_Core
CAT_PLOT = 1 # dpg.mvThemeCat_Plots
CAT_NODE = 2 # dpg.mvThemeCat_Nodes


Predicate = Callable[[str], bool]
Transform = Callable[[str], str]


@dataclass(frozen=True)
class NameRule:
    when: Predicate     # When Callable(NAME) returns TRUE
    then: Transform     # Then Callable(Name) returns STRING 
    note: str = ""      # NOTE about how this Rule works.



def pascal_to_kebab_case(string: str, *args, **kwargs) -> str:
    """ Convert PascalCase to kebab-case (handles acronyms like OMGThisIsNeat). """
    return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '-', string).lower()

# Tells the DSL naming processor to pre-proccess the name with this function BEFORE applying rules
PREPROCESSOR_FUNCTION = pascal_to_kebab_case 

NAME_RULES = {
    "color": {
        CAT_CORE: [
            NameRule(
                when=lambda name: name.startswith("plot-"),
                then=lambda name: f"color-{name}",
                note="Core colors: plot-* becomes color-plot-* to avoid plot namespace collision.",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: f"{name}-color",
                note="Core colors default to *-color.",
            ),
        ],
        CAT_PLOT: [
            NameRule(
                when=lambda name: name.startswith("plot-"),
                then=lambda name: name,
                note="Plot colors keep existing plot-* prefix.",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: f"plot-{name}",
                note="Plot colors default to plot-*.",
            ),
        ],
        CAT_NODE: [
            NameRule(
                when=lambda name: name.startswith("grid-"),
                then=lambda name: name.replace("grid-", "node-editor-", 1),
                note="Node colors: grid-* becomes node-editor-*.",
            ),
            NameRule(
                when=lambda name: name.startswith("node-"),
                then=lambda name: name.replace("node-", "nodes-", 1),
                note="Node colors: node-* becomes nodes-* to avoid awkward duplication.",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: f"node-{name}",
                note="Node colors default to node-*.",
            ),
        ],
    },

    "style": {
        CAT_CORE: [
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: name,
                note="Core styles keep their kebab-case name by default.",
            ),
        ],
        CAT_PLOT: [
            NameRule(
                when=lambda name: name.startswith("plot-"),
                then=lambda name: name,
                note="Plot styles keep existing plot-* prefix.",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: f"plot-{name}",
                note="Plot styles default to plot-*.",
            ),
        ],
        CAT_NODE: [
            NameRule(
                when=lambda name: name.startswith("grid-"),
                then=lambda name: name.replace("grid-", "node-editor-", 1),
                note="Node styles: grid-* becomes node-editor-*.",
            ),
            NameRule(
                when=lambda name: name.startswith("node-"),
                then=lambda name: name.replace("node-", "nodes-", 1),
                note="Node styles: node-* becomes nodes-* where needed.",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: f"node-{name}",
                note="Node styles default to node-*.",
            ),
        ],
    },
    "entity": {
        CAT_CORE: [
            NameRule(
                when=lambda name: name.startswith("window-"),
                then=lambda name: 'window',
                note="Replaces mvWindowAppItem as if it was called mvWindow",
            ),
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: name,
                note="Core entities are mostly unchanged",
            ),
        ],
        CAT_PLOT: [
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: name,
                note="Plot entities are unchanged",
            ),
        ],
        CAT_NODE: [
            NameRule(
                when=lambda name: True,                 # NOTE: Default Rule
                then=lambda name: name,
                note="Node entities are unchanged",
            ),
        ],
    },
}

__all__ = [
    "CAT_CORE", "CAT_PLOT", "CAT_NODE",                 # Category Constants
    "NAME_RULES", "PREPROCESSOR_FUNCTION",              # Naming Policy Rules
    "NameRule", "Predicate", "Transform",               # Rule-Related 
    "pascal_to_kebab_case"                              # PreProc Functions
]