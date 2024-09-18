# stdlib imports
import json
from pathlib import Path
from typing import Any, List, Protocol, Dict, Tuple, Type, Literal, Optional, Union
from abc import ABC, abstractmethod

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
        site_term: Type["SiteTerm"],
        fault_type: Optional[Literal["U", "SS", "NS", "RS"]],
        coefficients_table: Path,
        coefficients_list: List[str],  # TODO: #12 check actual need for such an object.
    ) -> None:
        self.magnitude = magnitude
        self.distance = distance
        self.building = building
        self.coefficients_table = coefficients_table
        self.coefficients_list = coefficients_list
        self.fault_type = fault_type
        self.event_function = event_term
        self.path_function = path_term
        self.site_function = site_term
        self._instantiate_functional_terms()

    def _instantiate_functional_terms(self) -> None:
        self.event_term = self.event_function(
            coefficients_table=self.coefficients_table,
            coefficients_list=self.coefficients_list,
            magnitude=self.magnitude,
            building=self.building,
            fault_type=self.fault_type,
        )
        self.path_term = self.path_function(
            coefficients_table=self.coefficients_table,
            coefficients_list=self.coefficients_list,
            magnitude=self.magnitude,
            distance=self.distance,
            building=self.building,
        )
        self.site_term = self.site_function(
            coefficient_table=self.coefficients_table,
            coefficients_list=self.coefficients_list,
            vs30=self.building.vs30,
            building=self.building,
        )

    def _change_attribute(self, obj: object, name: str, value: Any) -> None:
        setattr(self, name, value)
        self._instantiate_functional_terms()
        # TODO: #14 check how well this integrates.

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
        self._coefficients: Dict[str, float | int] = self._coefficients_lookup(
            self.coefficients_list
        )

    def _coefficients_lookup(self, lookup: List[Tuple[str]]) -> Dict:
        with open(self._coefficients_table, "r") as f:
            data = json.load(f)
        result = data
        coefficients = {}
        for i in lookup:
            coefficient_name = i[0]
            try:
                for o in map(str, i):
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
        building: Building,
        magnitude: float,
        distance: float,
    ) -> None:
        super().__init__(coefficients_table, coefficients_list, building)
        self.magnitude = magnitude
        self.distance = distance


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
        building: Building,
        magnitude: float,
    ) -> None:
        super().__init__(coefficients_table, coefficients_list, building)
        self.magnitude = magnitude


class SiteTerm(FunctionalTerm):
    """GMPE site term ABC.

    Attributes:
        coefficient_table (Path): path to coefficients table.
        coefficients_list (List(str))
        vs30 (float)
        pga_r (Optional(float))
        building (Building)
    """

    def __init__(
        self,
        coefficient_table: Path,
        coefficients_list: List[str],
        vs30: float,
        building: Building,
        pga_r: Optional[float] = None,
    ) -> None:
        super().__init__(
            coefficients_table=coefficient_table,
            coefficients_list=coefficients_list,
            building=building,
        )
        self.vs30 = vs30
        self.pga_r = pga_r
