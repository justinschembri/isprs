from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import json


@dataclass
class LineMapLine:
    """
    Represents the contents of a range of lines within a document to be parsed.

    Attributes:
        key (str): Descriptor (key) of the contents of a given block of text.
        start (int): The starting column corresponding to that block of text.
        stop (int): The finishing column (inclusive) corresponding to that block of text.
        map (dict[str,range]): A dict object containing the mapping and set in post-init.
    """

    line: int
    column_start: int
    column_end: int
    short_description: str
    line_map: Dict[int, List[Tuple[range, str]]] = field(
        init=False
    )  # post-init attribute

    def __post_init__(self):
        if self.column_start > self.column_end:
            raise ValueError(f"Column start must be greater than column finish.")
        self.line_map = {
            self.line: [
                (range(self.column_start, self.column_end), self.short_description)
            ]
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

if __name__ == '__main__':
    print(CSMIP_V2_LINEMAP)