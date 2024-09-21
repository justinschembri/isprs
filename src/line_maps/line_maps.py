from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import json


@dataclass
class LineMapLine:
    """
    Information model for a line from a linemap.

    A linemap is a set of integer and string descriptions which define what content is
    found at which line and within which column of some text based observation file.
    Example:

    ```
    line 1, columns 0 - 80: Observation Title
    line 2, columns 0 - 40: Observation Date
    line 2, columns 41 - 80: Observation Location
    ```

    Attributes:
        line (int)
        column_start (int)
        column_end (int)
        short_description (str)
        line_map_line (Dict[int, Tuple[range, str]]): post-init attribute where
        integer keys represent the line number, and the values are a 2 dimensional tuple
        of type range representing the column start and finish, and a string containing
        the short description.
    """

    line: int
    column_start: int
    column_end: int
    short_description: str
    line_map_line: Dict[int, Tuple[range, str]] = field(
        init=False
    )  # post-init attribute

    def __post_init__(self):
        if self.column_start > self.column_end:
            raise ValueError(f"Column start must be greater than column finish.")
        self.line_map_line = {
            self.line: (
                range(self.column_start, self.column_end),
                self.short_description,
            )
        }

    def __repr__(self):
        return (
            f"LineMapLine ({self.short_description}: Line: {self.line},"
            f"Columns: {self.column_start} → {self.column_end})"
        )


@dataclass
class LineMap:
    """
    A composition of LineMapLines.

    Attributes:
        source_name (str): Reference name of data-source to which the line map pertains.
        lines (List[LineMapLine])
    """

    source_name: str
    lines: List["LineMapLine"]

    def __repr__(self):
        return f"LineMap {self.source_name}: {len(self.lines)} lines"


def lineMap_parser(json_path: Path) -> "LineMap":
    """Parse a json line map and return a LineMap object.

    Args:
        json_path (Path): Path to JSON line map.

    Returns:
        LineMap object.
    """
    with open(json_path) as j:
        json_data = json.load(j)

    line_map_list = []
    for e in json_data["lines"]:
        line_map_list.append(
            LineMapLine(
                line=e["line"],
                column_start=e["column_start"],
                column_end=e["column_end"],
                short_description=e["short_description"],
            )
        )

        line_map = LineMap(source_name=json_data["source_name"], lines=line_map_list)
    return line_map


CSMIP_V2_LINEMAP = lineMap_parser("src/line_maps/csimp_v2.json")
