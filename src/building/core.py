# standard library imports:
from dataclasses import dataclass, field
from abc import ABC
import json
from pathlib import Path
from typing import Literal


@dataclass
class Building(ABC):
    """
    Building is an abstract base class (ABC) representing a building.

    Attributes:
        height (int | float): The height (metres) of the building.
        latitude (float): The latitude coordinate of the building.
        longitude (float): The longitude coordinate of the building.
        vs30 (float): The average shear-wave velocity in the top 30 meters of the soil.
        period (float): The fundamental period of the building, initialized later.

    Methods:
        ground() -> Building:
            Returns a new Building instance with default ground conditions (period = 0),
            used to calculate spectral acceleration.
    """

    height: int | float
    latitude: float
    longitude: float
    vs30: float
    period: float = field(init=False)

    def ground(self) -> "Building":
        return Building(
            height=self.height,
            latitude=self.latitude,
            longitude=self.longitude,
            period=0,
            vs30=760,
        )


@dataclass
class ASCEBuilding(Building):
    """
    ASCEBuilding is a subclass of Building with its natural period calculated using
    the ASCE7-10 methodology (equation 12.8.-7)

    Attributes:
        coefficients_table (Path): Path to JSON file containing model coefficients.
        structure_type (Literal): Type of the structure:
            - "Steel MRF"
            - "Concrete MRF"
            - "Eccentrically braced SF"
            - "Other systems"

    """

    coefficients_table: Path
    structure_type: Literal[
        "Steel MRF", "Concrete MRF", "Eccentrically braced SF", "Other systems"
    ]

    def __post_init__(self) -> None:

        self.period = self._calculate_natural_period()

    def _calculate_natural_period(self) -> float:
        with open(self.coefficients_table) as f:
            coefficients_data = json.load(f)
            coefficients = coefficients_data["coefficients"][
                self.structure_type
            ]  # type: dict
            ct = coefficients["Ct"]
            x = coefficients["x"]
            f.close()
        return ct * self.height**x
