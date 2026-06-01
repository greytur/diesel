import re
from typing import Mapping, Sequence
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