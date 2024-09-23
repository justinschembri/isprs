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
        lat (float): The latitude coordinate of the building.
        long (float): The longitude coordinate of the building.
        seismic_properties (Optional[SeismicProperties]): The seismic properties of the
            building, including details such as height and vs30 (average shear-wave
            velocity in the top 30 meters of the soil).

    Methods:
        ground() -> Building:
            Returns a new Building instance with ground seismic properties, where period
            is set to 0 and vs30 is set to 760 m/s (default ground condition).
            This method is used to calculate spectral acceleration.
    """

    latitude: float
    longitude: float
    seismic_properties: Optional["SeismicProperties"]

    def ground(self) -> "Building":
        return Building(
            latitude=self.latitude,
            longitude=self.longitude,
            seismic_properties=SeismicProperties(
                period=0, vs30=760, height=self.seismic_properties.properties["height"]
            ),
        )


class SeismicProperties:
    """
    Container class for seismic properties of a building.

    Attributes:
        period (Optional[int | float]): The fundamental period of the building, which
            can either be provided directly or calculated using a provided function.
        period_function (Optional[Callable[..., int | float]]): Pass a function to
            calculate the building's period from other passed properties.
        **kwargs: any seismic properties (e.g. height, vs30, structure type ...)

    Instantiation:
        if no period arg is passed, will calculate it from the passed period_function
        and other passed properties.
    """

    def __init__(
        self,
        period: Optional[Union[int, float]] = None,
        period_function: Optional[Callable[..., Union[int, float]]] = None,
        **kwargs
    ):
        self.period = period
        self.period_function = period_function
        self.properties = kwargs

        if self.period == None and self.period_function:
            self.period = self.period_function(**self.properties)

        if self.period == None and not self.period_function:
            raise ValueError(
                "Pass building period or function to calculate it from passed kwargs."
            )


def calculate_asce_period(
    structure_type: Literal[
        "Steel MRF", "Concrete MRF", "Eccentrically braced SF", "Other systems"
    ],
    height: Union[int, float],
    **kwargs
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
