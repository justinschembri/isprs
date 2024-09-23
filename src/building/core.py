# standard library imports:
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any, Callable, Literal, Optional, Union


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

    # height: int | float
    lat: float
    long: float
    seismic_properties: Optional["SeismicProperties"]
    # vs30: Optional[float] = None
    # period: Optional[float] = None

    def ground(self) -> "Building":
        return Building(
            lat=self.lat,
            long=self.long,
            seismic_properties=SeismicProperties(
                period=0, vs30=760, height=self.seismic_properties.properties["height"]
            ),
        )


class SeismicProperties:

    def __init__(
        self,
        period: Optional[Union[int, float]] = None,
        period_function: Optional[Callable[..., Union[int, float]]] = None,
        **kwargs
    ):
        self.period = period
        self.period_function = period_function
        self.properties = kwargs

        if not self.period and self.period_function:
            self.period = self.period_function(**self.kwargs)


def calculate_asce_period(
    *,
    structure_type: Literal[
        "Steel MRF", "Concrete MRF", "Eccentrically braced SF", "Other systems"
    ],
    height: Union[int, float]
) -> float:
    """Calculate the natural period using ASCE7-10 methodology (equation 12.8-7).

    Kwargs:
        structure_type (Literal): Type of the structure:
            - "Steel MRF"
            - "Concrete MRF"
            - "Eccentrically braced SF"
            - "Other systems
        height (int | float): Height of the building in metres.

    Returns:
        float: The calculated natural period.
    """
    COEFFICIENTS_TABLE = Path("src/building/coefficients/asce7-10.json")

    with open(COEFFICIENTS_TABLE) as f:
        coefficients_data = json.load(f)
        coefficients = coefficients_data["coefficients"][structure_type]  # type: dict
        ct = coefficients["Ct"]
        x = coefficients["x"]
    return ct * height**x
