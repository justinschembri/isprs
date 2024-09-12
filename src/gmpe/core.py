# stdlib imports
from typing import Protocol, Dict, Type, Literal, Optional
from abc import ABC

# external imports
# internal imports
from src.structures.core import Structure


class GMPE(ABC):
    def __init__(
        self,
        structure: "Structure",
        magnitude: float,
        rjb: float,
        event_term: Type["EventTerm"],
        path_term: Type["PathTerm"],
        fault_type: Optional[Literal["U", "SS", "NS", "RS"]],
    ) -> None:
        self.magnitude = magnitude
        self.rjb = rjb
        self.structure = structure
        self.event_term = event_term(magnitude=self.magnitude, structure=self.structure)
        self.path_term = path_term(
            magnitude=self.magnitude, rjb=self.rjb, structure=self.structure
        )
        self.fault_type = fault_type

    def calculate(self) -> float:
        pass


class PathTerm(Protocol):
    """GMPE path term protocol.

    Attributes:
        magnitude (float): Moment magnitude.
        rjb (float): RJB distance.
        structure ("Structure"): Structure under examination.
    """

    def __init__(self, magnitude:float, rjb:float, structure:"Structure") -> None:
        ...

    def _coefficient_lookup(self) -> Dict: ...
    def calculate(self) -> float: ...


class EventTerm(Protocol):
    """GMPE event term protocol.

    Attributes:
        magnitude (float): Moment magnitude.
        structure ("Structure"): Structure under examination.
    """

    def __init__(self, magnitude:float, structure:"Structure") -> None:
        ...

    def _coefficient_lookup(self) -> Dict: ...
    def calculate(self) -> float: ...

class SiteTerm(Protocol):
    """GMPE site term protocol.

    Attributes:
        vs30: Shear Wave Velocity over the top 30 meters.
    """
    def __init__(self, vs30:float, pga_r: Optional[float]) -> None: 
        ...
    
    def _coefficient_lookup(self) -> Dict: ...
    def calculate(self) -> float: ...
