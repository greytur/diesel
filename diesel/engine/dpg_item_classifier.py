"""
DIESEL DearPyGUI item type classifier.

This module enriches DearPyGUI mvAppItemType names with stable metadata:

    domain      -> handler | registry | value | asset | theming | element | special
    dimension   -> container | item
    category    -> 0 | 1 | 2
    source      -> dpg | imgui | implot | imnodes
    role        -> optional secondary documentation/schema hint

It is designed for builder-time use. Runtime DSL code should consume the
aggregated metadata artifact instead of re-classifying item types.

The classifier intentionally keeps concepts separate:

- domain does not encode plot/node/draw variants
- category encodes core/plot/node backend family
- source is descriptive
- dimension is derived from DPG parent/child metadata when possible
- role is an optional, non-authoritative hint

No external package dependency is required.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum, Enum
import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from tools import read_file, save_json

# =============================================================================
# Public enums / constants
# =============================================================================

class StrEnum(str, Enum):
    """Custom StrEnum implementation to support Python versions before 3.11."""
    def __str__(self) -> str:
        return self.value

class Domain(StrEnum):
    HANDLER = "handler"
    REGISTRY = "registry"
    VALUE = "value"
    ASSET = "asset"
    THEMING = "theming"
    ELEMENT = "element"
    SPECIAL = "special"


class Dimension(StrEnum):
    CONTAINER = "container"
    ITEM = "item"


class Category(IntEnum):
    CORE = 0
    PLOT = 1
    NODE = 2


class Source(StrEnum):
    DPG = "dpg"
    IMGUI = "imgui"
    IMPLOT = "implot"
    IMNODES = "imnodes"


# These are explicit exceptions. They must be checked before name-derived rules.
SPECIAL_ITEMS: frozenset[str] = frozenset(
    {
        "mvFileExtension",
        "mvDragPayload",
        "mvStage",
        "mvTemplateRegistry",
        "mvFontChars",
        "mvFontRange",
        "mvFontRangeHint",
    }
)

ASSET_ITEMS: frozenset[str] = frozenset(
    {
        "mvFont",
        "mvStaticTexture",
        "mvDynamicTexture",
        "mvRawTexture",
        "mvColorMap",
        "mvCharRemap",
    }
)

# Filter: CONTAINS "Draw"
# mvDraw[^Na-z][^a][A-Za-z]+
DRAW_COMMAND_ITEMS: frozenset[str] = frozenset(
    {
        "mvDrawLine",
        "mvDrawArrow",
        "mvDrawTriangle",
        "mvDrawImageQuad",
        "mvDrawCircle",
        "mvDrawEllipse",
        "mvDrawBezierCubic",
        "mvDrawBezierQuadratic",
        "mvDrawQuad",
        "mvDrawRect",
        "mvDrawText",
        "mvDrawPolygon",
        "mvDrawPolyline",
        "mvDrawImage",
    }
)

# Filter: CONTAINS "Draw"
# Filter: Not in "mvDraw[^Na-z][^a][A-Za-z]+"
DRAW_CONTAINER_ITEMS: frozenset[str] = frozenset(
    {
        "mvDrawlist",
        "mvViewportDrawlist",
        "mvDrawLayer",
        "mvDrawNode",
    }
)

# Conservative fallback used only when parsed DPG parent/child metadata is absent.
# Prefer deriving containers from allowable-parent data.
FALLBACK_CONTAINER_ITEMS: frozenset[str] = frozenset(
    {
        "mvWindowAppItem",
        "mvChildWindow",
        "mvGroup",
        "mvTabBar",
        "mvTab",
        "mvMenuBar",
        "mvViewportMenuBar",
        "mvMenu",
        "mvTooltip",
        "mvCollapsingHeader",
        "mvTreeNode",
        "mvFileDialog",
        "mvFilterSet",
        "mvClipper",
        "mvTable",
        "mvTableRow",
        "mvTableCell",
        "mvNodeEditor",
        "mvNode",
        "mvNodeAttribute",
        "mvPlot",
        "mvSubPlots",
        "mvPlotAxis",
        "mvDrawlist",
        "mvViewportDrawlist",
        "mvDrawLayer",
        "mvDrawNode",
        "mvStage",
        "mvDragPayload",
        "mvTextureRegistry",
        "mvFontRegistry",
        "mvHandlerRegistry",
        "mvItemHandlerRegistry",
        "mvTheme",
        "mvThemeComponent",
        "mvValueRegistry",
        "mvColorMapRegistry",
        "mvTemplateRegistry",
    }
)


# Complete item list from the mvAppItemTypes.inc content.
# This is useful for tests, bootstrapping, and direct JSON generation.
MV_APP_ITEM_TYPES_V2_0: tuple[str, ...] = (
    "mvInputText",
    "mvButton",
    "mvRadioButton",
    "mvTabBar",
    "mvTab",
    "mvImage",
    "mvMenuBar",
    "mvViewportMenuBar",
    "mvMenu",
    "mvMenuItem",
    "mvChildWindow",
    "mvGroup",
    "mvSliderFloat",
    "mvSliderInt",
    "mvFilterSet",
    "mvDragFloat",
    "mvDragInt",
    "mvInputFloat",
    "mvInputInt",
    "mvColorEdit",
    "mvClipper",
    "mvColorPicker",
    "mvTooltip",
    "mvCollapsingHeader",
    "mvSeparator",
    "mvCheckbox",
    "mvListbox",
    "mvText",
    "mvCombo",
    "mvPlot",
    "mvSimplePlot",
    "mvDrawlist",
    "mvWindowAppItem",
    "mvSelectable",
    "mvTreeNode",
    "mvProgressBar",
    "mvSpacer",
    "mvImageButton",
    "mvTimePicker",
    "mvDatePicker",
    "mvColorButton",
    "mvFileDialog",
    "mvTabButton",
    "mvDrawNode",
    "mvNodeEditor",
    "mvNode",
    "mvNodeAttribute",
    "mvTable",
    "mvTableColumn",
    "mvTableRow",
    "mvDrawLine",
    "mvDrawArrow",
    "mvDrawTriangle",
    "mvDrawImageQuad",
    "mvDrawCircle",
    "mvDrawEllipse",
    "mvDrawBezierCubic",
    "mvDrawBezierQuadratic",
    "mvDrawQuad",
    "mvDrawRect",
    "mvDrawText",
    "mvDrawPolygon",
    "mvDrawPolyline",
    "mvDrawImage",
    "mvDragFloatMulti",
    "mvDragIntMulti",
    "mvSliderFloatMulti",
    "mvSliderIntMulti",
    "mvInputIntMulti",
    "mvInputFloatMulti",
    "mvDragPoint",
    "mvDragLine",
    "mvDragRect",
    "mvAnnotation",
    "mvAxisTag",
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
    "mvColorMapScale",
    "mvSlider3D",
    "mvKnobFloat",
    "mvLoadingIndicator",
    "mvNodeLink",
    "mvTextureRegistry",
    "mvStaticTexture",
    "mvDynamicTexture",
    "mvStage",
    "mvDrawLayer",
    "mvViewportDrawlist",
    "mvFileExtension",
    "mvPlotLegend",
    "mvPlotAxis",
    "mvHandlerRegistry",
    "mvKeyDownHandler",
    "mvKeyPressHandler",
    "mvKeyReleaseHandler",
    "mvMouseMoveHandler",
    "mvMouseWheelHandler",
    "mvMouseClickHandler",
    "mvMouseDoubleClickHandler",
    "mvMouseDownHandler",
    "mvMouseReleaseHandler",
    "mvMouseDragHandler",
    "mvHoverHandler",
    "mvActiveHandler",
    "mvFocusHandler",
    "mvVisibleHandler",
    "mvEditedHandler",
    "mvActivatedHandler",
    "mvDeactivatedHandler",
    "mvDeactivatedAfterEditHandler",
    "mvToggledOpenHandler",
    "mvClickedHandler",
    "mvDoubleClickedHandler",
    "mvDragPayload",
    "mvResizeHandler",
    "mvFont",
    "mvFontRegistry",
    "mvTheme",
    "mvThemeColor",
    "mvThemeStyle",
    "mvThemeComponent",
    "mvFontRangeHint",
    "mvFontRange",
    "mvFontChars",
    "mvCharRemap",
    "mvValueRegistry",
    "mvIntValue",
    "mvFloatValue",
    "mvFloat4Value",
    "mvInt4Value",
    "mvBoolValue",
    "mvStringValue",
    "mvDoubleValue",
    "mvDouble4Value",
    "mvColorValue",
    "mvFloatVectValue",
    "mvSeriesValue",
    "mvRawTexture",
    "mvSubPlots",
    "mvColorMap",
    "mvColorMapRegistry",
    "mvColorMapButton",
    "mvColorMapSlider",
    "mvTemplateRegistry",
    "mvTableCell",
    "mvItemHandlerRegistry",
    "mvInputDouble",
    "mvInputDoubleMulti",
    "mvDragDouble",
    "mvDragDoubleMulti",
    "mvSliderDouble",
    "mvSliderDoubleMulti",
    "mvCustomSeries",
)


PLOT_CATEGORY_ITEMS_REGEX = re.compile(
    r"mv(?:.*(?:Axis.*|Plot.*)|.*Series|ColorMap.*|Anno.*|Drag[PLR][oie].*)"
)


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class ItemTraits:
    domain:         Domain
    dimension:      Dimension
    category:       Category
    source:         Source
    role:           str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain.value,
            "dimension": self.dimension.value,
            "category": int(self.category),
            "source": self.source.value,
            "role": self.role,
        }


@dataclass(frozen=True, slots=True)
class ItemClassification:
    dpg:        str
    traits:     ItemTraits

    def to_dict(self) -> dict[str, Any]:
        return {
            "dpg": self.dpg,
            "traits": self.traits.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    items:              dict[str, ItemClassification]
    parent_map:         dict[str, list[str]]
    container_names:    set[str]
    warnings:           list[str]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "items": {
                name: classification.to_dict()
                for name, classification in self.items.items()
            },
            "parent_map": self.parent_map,
            "container_names": sorted(self.container_names),
            "warnings": self.warnings,
        }


# =============================================================================
# Parsing helpers
# =============================================================================


def parse_mv_item_types_inc(source: str) -> list[str]:
    """
    Extract mvAppItemType names from mvAppItemTypes.inc-style source.

    Supports entries like:

        X( mvButton ) \\
        X(mvButton)
    """
    return re.findall(r"X\(\s*(mv[A-Za-z0-9]+)\s*\)", source)


def parse_allowable_parents(cpp_source: str) -> dict[str, list[str]]:
    """
    Parse a DearPyGUI GetAllowableParents-style switch body.

    Expected C++ shape:

        case mvAppItemType::mvButton:
            MV_START_PARENTS
            MV_ADD_PARENT(mvAppItemType::mvWindowAppItem)
            MV_ADD_PARENT(mvAppItemType::mvGroup)
            MV_END_PARENTS

    Returns:

        {
            "mvButton": ["mvWindowAppItem", "mvGroup"]
        }
    """
    case_re = re.compile(
        r"case\s+mvAppItemType::(?P<item>mv[A-Za-z0-9]+):\s*"
        r"MV_START_PARENTS"
        r"(?P<body>.*?)"
        r"MV_END_PARENTS",
        re.DOTALL,
    )
    parent_re = re.compile(
        r"MV_ADD_PARENT\(\s*mvAppItemType::(?P<parent>mv[A-Za-z0-9]+)\s*\)"
    )

    parent_map: dict[str, list[str]] = {}

    for match in case_re.finditer(cpp_source):
        item_name = match.group("item")
        body = match.group("body")
        parent_map[item_name] = parent_re.findall(body)

    return parent_map


def parse_allowable_children(cpp_source: str) -> dict[str, list[str]]:
    """
    Parse a hypothetical or matching DearPyGUI GetAllowableChildren-style switch.

    This accepts the same macro pattern as parse_allowable_parents but reads
    MV_ADD_CHILD instead of MV_ADD_PARENT.

    The function is included so the builder can support either direction if the
    upstream source exposes children instead of parents.
    """
    case_re = re.compile(
        r"case\s+mvAppItemType::(?P<item>mv[A-Za-z0-9]+):\s*"
        r"MV_START_CHILDREN"
        r"(?P<body>.*?)"
        r"MV_END_CHILDREN",
        re.DOTALL,
    )
    child_re = re.compile(
        r"MV_ADD_CHILD\(\s*mvAppItemType::(?P<child>mv[A-Za-z0-9]+)\s*\)"
    )

    child_map: dict[str, list[str]] = {}

    for match in case_re.finditer(cpp_source):
        item_name = match.group("item")
        body = match.group("body")
        child_map[item_name] = child_re.findall(body)

    return child_map


def derive_container_names_from_parent_map(
    parent_map: Mapping[str, Sequence[str]],
) -> set[str]:
    """
    If an item appears as a valid parent, it can contain at least one child.
    """
    container_names: set[str] = set()

    for parents in parent_map.values():
        container_names.update(parents)

    return container_names


def derive_container_names_from_child_map(
    child_map: Mapping[str, Sequence[str]],
) -> set[str]:
    """
    If upstream exposes a parent -> children map, every key with children is a
    container.
    """
    return {
        item_name
        for item_name, children in child_map.items()
        if len(children) > 0
    }


# =============================================================================
# Classification
# =============================================================================


def classify_domain(item_name: str) -> Domain:
    """
    Return the exclusive domain for an item name.

    Order is intentional:
        special -> theming -> handler -> registry -> value -> asset -> element
    """
    if item_name in SPECIAL_ITEMS:
        return Domain.SPECIAL
    if "Theme" in item_name:
        return Domain.THEMING
    if "Handler" in item_name and "Registry" not in item_name:
        return Domain.HANDLER
    if item_name.endswith("Registry"):
        return Domain.REGISTRY
    if item_name.endswith("Value"):
        return Domain.VALUE
    if item_name in ASSET_ITEMS:
        return Domain.ASSET
    return Domain.ELEMENT


def classify_category(item_name: str) -> Category:
    """
    Return backend family category.

        0 = CORE DearPyGUI / Dear ImGui
        1 = ImPlot
        2 = ImNodes
    """
    if item_name.startswith("mvNode"):
        return Category.NODE
    if PLOT_CATEGORY_ITEMS_REGEX.fullmatch(item_name):             #if item_name in PLOT_CATEGORY_ITEMS:
        return Category.PLOT
    return Category.CORE


def classify_source(item_name: str, domain: Domain, category: Category) -> Source:
    """
    Return descriptive source label.

    Category is authoritative for ImPlot and imnodes. For core category, normal
    UI elements are ImGui-backed while DPG infrastructure is source='dpg'.
    """
    if category is Category.NODE:
        return Source.IMNODES

    if category is Category.PLOT:
        return Source.IMPLOT

    if domain in {
        Domain.HANDLER,
        Domain.REGISTRY,
        Domain.VALUE,
        Domain.ASSET,
        Domain.THEMING,
        Domain.SPECIAL,
    }:
        return Source.DPG

    return Source.IMGUI


def classify_dimension(
    item_name: str,
    container_names: set[str] | None = None,
    *,
    use_fallback_containers: bool = True,
) -> Dimension:
    """
    Return whether the item can contain children.

    Prefer a container_names set derived from DearPyGUI parent/child metadata.

    If no set is provided and use_fallback_containers=True, a conservative static
    fallback is used. This fallback is intended for bootstrapping only.
    """
    if container_names is not None:
        return (
            Dimension.CONTAINER
            if item_name in container_names
            else Dimension.ITEM
        )

    if use_fallback_containers and item_name in FALLBACK_CONTAINER_ITEMS:
        return Dimension.CONTAINER

    return Dimension.ITEM


def classify_role(
    item_name: str,
    domain: Domain,
    category: Category,
    dimension: Dimension,
) -> str | None:
    match domain:
        case Domain.HANDLER:
            return "handler"
        case Domain.REGISTRY:
            return registry_role(item_name)
        case Domain.VALUE:
            return "value"
        case Domain.ASSET:
            return asset_role(item_name)
        case Domain.THEMING:
            return theming_role(item_name)
        case Domain.SPECIAL:
            return special_role(item_name)
        case Domain.ELEMENT:
            return element_role(item_name, category, dimension)
        case _:
            return None


def registry_role(item_name: str) -> str:
    registry_roles = {
        "mvTextureRegistry":        "texture-registry",
        "mvFontRegistry":           "font-registry",
        "mvHandlerRegistry":        "handler-registry",
        "mvItemHandlerRegistry":    "item-handler-registry",
        "mvValueRegistry":          "value-registry",
        "mvColorMapRegistry":       "colormap-registry",
    }
    return registry_roles.get(item_name, "registry")


def asset_role(item_name: str) -> str:
    if item_name == "mvFont":
        return "font"
    if item_name in {"mvStaticTexture", "mvDynamicTexture", "mvRawTexture"}:    # if "Texture" in item_name may be faster???
        return "texture"
    if item_name == "mvColorMap":
        return "colormap"
    if item_name == "mvCharRemap":
        return "char-remap"
    return "asset"


def theming_role(item_name: str) -> str:
    theming_roles = {
        "mvTheme":              "theme",
        "mvThemeComponent":     "theme-component",
        "mvThemeColor":         "theme-color",
        "mvThemeStyle":         "theme-style",
    }
    return theming_roles.get(item_name, "theming")


def special_role(item_name: str) -> str:
    if item_name == "mvStage":
        return "stage"
    if item_name == "mvTemplateRegistry":
        return "template-registry"
    if item_name == "mvFileExtension":
        return "file-extension"
    if item_name == "mvDragPayload":
        return "payload"
    if item_name in {"mvFontChars", "mvFontRange", "mvFontRangeHint"}:  # if "Font" in item_name may be faster???
        return "legacy-font-range"
    return "special"


def element_role(
    item_name: str,
    category: Category,
    dimension: Dimension,
) -> str:
    if category is Category.NODE:
        node_roles = {
            "mvNodeEditor":     "node-editor",
            "mvNode":           "node",
            "mvNodeAttribute":  "node-attribute",
            "mvNodeLink":       "node-link",
        }
        return node_roles.get(item_name, "node-item")

    if category is Category.PLOT:
        if item_name.endswith("Series"):
            return "plot-series"

        plot_roles = {
            "mvPlot":               "plot",
            "mvSimplePlot":         "plot",
            "mvSubPlots":           "plot",
            "mvPlotAxis":           "plot-axis",
            "mvAxisTag":            "plot-axis",
            "mvPlotLegend":         "plot-legend",
            "mvAnnotation":         "plot-annotation",
            "mvDragPoint":          "plot-drag-control",
            "mvDragLine":           "plot-drag-control",
            "mvDragRect":           "plot-drag-control",
            "mvColorMapButton":     "colormap-control",
            "mvColorMapSlider":     "colormap-control",
            "mvColorMapScale":      "colormap-control",
        }
        return plot_roles.get(item_name, "plot-item")

    if item_name in DRAW_CONTAINER_ITEMS:
        return "draw-container"

    if item_name in DRAW_COMMAND_ITEMS:
        return "drawing-command"

    core_roles = {
        "mvWindowAppItem":      "window",
        "mvChildWindow":        "window",
        "mvGroup":              "layout",
        "mvSpacer":             "layout",
        "mvSeparator":          "layout",
        "mvTabBar":             "tab",
        "mvTab":                "tab",
        "mvTabButton":          "tab",
        "mvMenuBar":            "menu",
        "mvViewportMenuBar":    "menu",
        "mvMenu":               "menu",
        "mvMenuItem":           "menu",
        "mvTable":              "table",
        "mvTableRow":           "table",
        "mvTableCell":          "table",
        "mvTableColumn":        "table-column",
        "mvTooltip":            "tooltip",
        "mvCollapsingHeader":   "collapsing-header",
        "mvTreeNode":           "tree-node",
        "mvFileDialog":         "file-dialog",
        "mvFilterSet":          "filter-set",
        "mvClipper":            "clipper",
        "mvImage":              "image",
        "mvImageButton":        "image-button",
        "mvColorEdit":          "color",
        "mvColorPicker":        "color",
        "mvColorButton":        "color",
        "mvSlider3D":           "slider-3d",
        "mvKnobFloat":          "knob",
        "mvLoadingIndicator":   "loading-indicator",
    }

    if item_name in core_roles:
        return core_roles[item_name]
    if dimension is Dimension.CONTAINER:
        return "container-widget"
    return "widget"


def classify_item_type(
    item_name: str,
    container_names: set[str] | None = None,
    *,
    use_fallback_containers: bool = True,
) -> ItemClassification:
    domain = classify_domain(item_name)
    category = classify_category(item_name)
    source = classify_source(item_name, domain, category)
    dimension = classify_dimension(
        item_name,
        container_names,
        use_fallback_containers=use_fallback_containers,
    )
    role = classify_role(item_name, domain, category, dimension)

    traits = ItemTraits(
        domain=domain,
        dimension=dimension,
        category=category,
        source=source,
        role=role,
    )
    return ItemClassification(dpg=item_name, traits=traits)


def classify_item_types(
    item_names: Iterable[str],
    container_names: set[str] | None = None,
    *,
    use_fallback_containers: bool = True,
) -> dict[str, ItemClassification]:
    return {
        item_name: classify_item_type(
            item_name,
            container_names,
            use_fallback_containers=use_fallback_containers,
        )
        for item_name in item_names
    }


# =============================================================================
# Validation
# =============================================================================


class ClassificationError(ValueError):
    """Raised when classifier output violates the model."""


def validate_classification(
    item_name: str,
    classification: ItemClassification,
) -> list[str]:
    warnings: list[str] = []
    traits = classification.traits

    if traits.category not in {Category.CORE, Category.PLOT, Category.NODE}:
        raise ClassificationError(
            f"{item_name}: invalid category {traits.category!r}."
        )

    if traits.dimension not in {Dimension.CONTAINER, Dimension.ITEM}:
        raise ClassificationError(
            f"{item_name}: invalid dimension {traits.dimension!r}."
        )

    if traits.domain is Domain.HANDLER and (
        "Handler" not in item_name or "Registry" in item_name
    ):
        raise ClassificationError(
            f"{item_name}: handler domain violates handler naming rule."
        )

    if "Theme" in item_name and item_name not in SPECIAL_ITEMS:
        if traits.domain is not Domain.THEMING:
            raise ClassificationError(
                f"{item_name}: item contains 'Theme' but is not theming."
            )

    if item_name.endswith("Registry") and item_name not in SPECIAL_ITEMS:
        if traits.domain is not Domain.REGISTRY:
            raise ClassificationError(
                f"{item_name}: registry-like item is not registry."
            )

    if item_name.endswith("Value") and traits.domain is not Domain.VALUE:
        raise ClassificationError(
            f"{item_name}: value-like item is not value."
        )

    if PLOT_CATEGORY_ITEMS_REGEX.fullmatch(item_name) and traits.category is not Category.PLOT:
        raise ClassificationError(
            f"{item_name}: expected plot category."
        )

    if item_name.startswith("mvNode") and traits.category is not Category.NODE:
        raise ClassificationError(
            f"{item_name}: expected node category."
        )

    if traits.category is Category.PLOT and traits.source is not Source.IMPLOT:
        raise ClassificationError(
            f"{item_name}: plot category must have source='implot'."
        )

    if traits.category is Category.NODE and traits.source is not Source.IMNODES:
        raise ClassificationError(
            f"{item_name}: node category must have source='imnodes'."
        )

    if traits.category is Category.CORE and traits.source in {
        Source.IMPLOT,
        Source.IMNODES,
    }:
        raise ClassificationError(
            f"{item_name}: core category cannot use plot/node source."
        )

    if traits.domain is Domain.REGISTRY and item_name in ASSET_ITEMS:
        raise ClassificationError(
            f"{item_name}: asset item cannot classify as registry."
        )

    if item_name == "mvFont" and traits.domain is not Domain.ASSET:
        raise ClassificationError("mvFont must classify as asset.")

    if item_name == "mvFont" and traits.dimension is Dimension.CONTAINER:
        warnings.append(
            "mvFont classified as container. Confirm this came from parsed "
            "target-version parent/child metadata, not context-manager presence alone."
        )

    if item_name in {"mvFontChars", "mvFontRange", "mvFontRangeHint"}:
        if traits.domain is not Domain.SPECIAL:
            raise ClassificationError(
                f"{item_name}: legacy font range item must be special."
            )

    if item_name == "mvDragPayload" and traits.domain is not Domain.SPECIAL:
        raise ClassificationError("mvDragPayload must classify as special.")

    if item_name == "mvTableColumn" and traits.domain is not Domain.ELEMENT:
        raise ClassificationError("mvTableColumn must classify as element.")

    return warnings


def validate_classifications(
    classifications: Mapping[str, ItemClassification],
) -> list[str]:
    warnings: list[str] = []

    for item_name, classification in classifications.items():
        warnings.extend(validate_classification(item_name, classification))

    return warnings


# =============================================================================
# Builder-level APIs
# =============================================================================


def build_classification_report(
    item_names: Iterable[str],
    *,
    allowable_parents_source: str | None = None,
    allowable_children_source: str | None = None,
    container_names: set[str] | None = None,
    use_fallback_containers: bool = True,
) -> ClassificationReport:
    """
    Build a complete classification report.

    Container source priority:
        1. explicit container_names argument
        2. derived from allowable_children_source
        3. derived from allowable_parents_source
        4. fallback static container set, if enabled
    """
    parent_map: dict[str, list[str]] = {}
    derived_containers: set[str] | None = None

    if container_names is not None:
        derived_containers = set(container_names)

    elif allowable_children_source:
        child_map = parse_allowable_children(allowable_children_source)
        derived_containers = derive_container_names_from_child_map(child_map)

    elif allowable_parents_source:
        parent_map = parse_allowable_parents(allowable_parents_source)
        derived_containers = derive_container_names_from_parent_map(parent_map)

    elif use_fallback_containers:
        derived_containers = set(FALLBACK_CONTAINER_ITEMS)

    classifications = classify_item_types(
        item_names,
        derived_containers,
        use_fallback_containers=use_fallback_containers,
    )
    warnings = validate_classifications(classifications)

    return ClassificationReport(
        items=classifications,
        parent_map=parent_map,
        container_names=derived_containers or set(),
        warnings=warnings,
    )


def enrich_existing_item_record(
    record: Mapping[str, Any],
    *,
    container_names: set[str] | None = None,
    use_fallback_containers: bool = True,
    dpg_key: str = "dpg",
) -> dict[str, Any]:
    """
    Add or replace record['traits'] for an existing aggregator item record.

    The input record is copied. The original mapping is not mutated.
    """
    if dpg_key not in record:
        raise KeyError(f"Record is missing required key {dpg_key!r}.")

    item_name = str(record[dpg_key])
    classification = classify_item_type(
        item_name,
        container_names,
        use_fallback_containers=use_fallback_containers,
    )

    enriched = dict(record)
    existing_traits = dict(enriched.get("traits") or {})
    existing_traits.update(classification.traits.to_dict())
    enriched["traits"] = existing_traits
    return enriched


def enrich_existing_item_records(
    records: Iterable[Mapping[str, Any]],
    *,
    container_names: set[str] | None = None,
    use_fallback_containers: bool = True,
    dpg_key: str = "dpg",
) -> list[dict[str, Any]]:
    return [
        enrich_existing_item_record(
            record,
            container_names=container_names,
            use_fallback_containers=use_fallback_containers,
            dpg_key=dpg_key,
        )
        for record in records
    ]


# =============================================================================
# CLI
# =============================================================================


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify DearPyGUI mvAppItemType names."
    )
    parser.add_argument(
        "--item-types-inc",
        type=Path,
        default=None,
        help="Path to mvAppItemTypes.inc. If omitted, the built-in v2.0 list is used.",
    )
    parser.add_argument(
        "--allowable-parents",
        type=Path,
        default=None,
        help="Path to C++ source containing GetAllowableParents-style macros.",
    )
    parser.add_argument(
        "--allowable-children",
        type=Path,
        default=None,
        help="Path to C++ source containing GetAllowableChildren-style macros.",
    )
    parser.add_argument(
        "--no-fallback-containers",
        action="store_true",
        help="Do not use the static fallback container list.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.item_types_inc:
        item_names = parse_mv_item_types_inc(read_file(args.item_types_inc))
    else:
        item_names = list(MV_APP_ITEM_TYPES_V2_0)

    allowable_parents_source = (
        read_file(args.allowable_parents)
        if args.allowable_parents
        else None
    )
    allowable_children_source = (
        read_file(args.allowable_children)
        if args.allowable_children
        else None
    )

    report = build_classification_report(
        item_names,
        allowable_parents_source=allowable_parents_source,
        allowable_children_source=allowable_children_source,
        use_fallback_containers=not args.no_fallback_containers,
    )
    jsonable = report.to_jsonable()

    if args.output:
        save_json(args.output, jsonable)
    else:
        print(json.dumps(jsonable, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
