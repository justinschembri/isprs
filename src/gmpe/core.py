# stdlib imports
import json
from pathlib import Path
from typing import List, Protocol, Dict, Tuple, Type, Literal, Optional, Union
from abc import ABC, abstractmethod, abs

# external imports
# internal imports
from src.building.core import Building


class GMPE(ABC):
    def __init__(
        self,
        building: "Building",
        magnitude: float,
        distance: float,
        event_term: Type["EventTerm"],
        path_term: Type["PathTerm"],
        fault_type: Optional[Literal["U", "SS", "NS", "RS"]],
        coefficients_table: Path,
        coefficients_list: List[str],
    ) -> None:
        self.magnitude = magnitude
        self.distance = distance
        self.building = building
        self.event_term = event_term(
            coefficients_table=self.coefficients_table,
            coefficients_list=self.coefficients_list,
            magnitude=self.magnitude,
            building=self.building,
        )
        self.path_term = path_term(
            coefficients_table=self.coefficients_table,
            coefficients_list=self.coefficients_list,
            magnitude=self.magnitude,
            distance=self.distance,
            building=self.building,
        )
        self.fault_type = fault_type
        self.coefficients_table = coefficients_table
        self.coefficients_list = coefficients_list

    @abstractmethod
    def calculate(self) -> float:
        pass


class FunctionalTerm(ABC):
    """Generic baseclass for a functional term within a GMPE.

    Base class assumes the use of coefficients and a calculate function.

    Attributes:
        ...
    """

    def __init__(
        self,
        coefficients_table: Path,
        coefficients_list: List[str],
        building: "Building",
    ) -> None:
        self.building = building
        self._coefficients_table = coefficients_table
        self.coefficients_list = coefficients_list
        self.coefficients: Dict[str, float | int] = self._coefficient_lookup()

    def _coefficients_lookup(self, lookup: List[Tuple[str]]) -> Dict:
        with open(self._coefficients_table, "r") as f:
            data = json.load(f)
        result = data
        coefficients = {}
        for i in lookup:
            coefficient_name = i[0]
            try:
                for o in i:
                    result = result[o]
            except KeyError:
                raise ValueError(
                    f"Invalid key sequence: {' -> '.join(map(str, lookup))}"
                )
            coefficients.update({coefficient_name: result})
            result = data
        return coefficients

    @abstractmethod
    def calculate(self) -> float:
        pass


class PathTerm(FunctionalTerm):
    """GMPE path term protocol.

    Attributes:
        coefficients_table (Path): path to coefficients table.
        coefficients_list (Path): list of relevant coefficients to lookup.
        magnitude (float): Moment magnitude.
        distance (float): Source to site distance.
        building ("building"): building under examination.
    """

    def __init__(
        self,
        coefficients_table: Path,
        coefficients_list: List[str],
        magnitude: float,
        distance: float,
        building: "Building",
    ) -> None:
        super().__init__(self, coefficients_table, coefficients_list)
        self.magnitude = magnitude
        self.distance = distance
        self.building = building


class EventTerm(FunctionalTerm):
    """GMPE event term protocol.

    Attributes:
        coefficients_table (Path): path to coefficients table.
        coefficients_list (Path): list of relevant coefficients to lookup.
        magnitude (float): Moment magnitude.
        building ("building"): building under examination.
    """

    def __init__(
        self,
        coefficients_table: Path,
        coefficients_list: List[str],
        magnitude: float,
        building: "Building",
    ) -> None:
        super().__init__(
            coefficients_table=coefficients_table, coefficients_list=coefficients_list
        )
        self.magnitude = magnitude
        self.building = building


class SiteTerm(FunctionalTerm):
    """GMPE site term protocol.

    Attributes:
        coefficients_table (Path): path to coefficients table.
        coefficients_list (Path): list of relevant coefficients to lookup.
        vs30: Shear Wave Velocity over the top 30 meters.
        pga_r (Optional[float]): Calculated PGA for an event without the site
        attenuation function (i.e., in rock with vs = 760m/s)
    """

    def __init__(
        self,
        coefficient_table: Path,
        coefficients_list: List[str],
        vs30: float,
        pga_r: Optional[float],
        building: Building,
    ) -> None:
        super().__init__(
            coefficients_table=coefficient_table,
            coefficients_list=coefficients_list,
            building=building,
        )
        self.vs30 = vs30
        self.pga_r = pga_r
