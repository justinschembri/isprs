# stdlib imports
import numpy as np
from typing import Dict, Literal, Type, Optional

# external imports

# internal imports
from src.gmpe.core import GMPE, PathTerm, EventTerm, SiteTerm
from src.structures.core import Structure


class BSSA13GMPE(GMPE):
    def __init__(
        self,
        structure: Structure,
        magnitude: float,
        rjb: float,
        event_term: Type[EventTerm],
        path_term: Type[PathTerm],
        fault_type: Optional[Literal["U", "SS", "NS", "RS"]],
    ) -> None:
        super().__init__(structure, magnitude, rjb, event_term, path_term, fault_type)

    def _calculate_unamplified_pga(self) -> float:
        ground = self.structure.__setattr__("period", 0)
        event_term = BSSA13EventTerm(
            magnitude=self.magnitude, structure=self.structure.ground()
        )
        path_term = BSSA13PathTerm(
            magnitude=self.magnitude, rjb=self.rjb, structure=self.structure.ground()
        )
        return event_term.calculate() + path_term.calculate()

    def calculate(self) -> float:
        event_term = BSSA13EventTerm(magnitude=self.magnitude, structure=self.structure)
        path_term = BSSA13PathTerm(
            magnitude=self.magnitude, rjb=self.rjb, structure=self.structure
        )
        site_term = BSSA13SiteTerm(
            vs30=self.structure.vs30, pga_r=self._calculate_unamplified_pga()
        )

        return event_term.calculate() + path_term.calculate() + site_term.calculate()


class BSSA13PathTerm(PathTerm):
    def __init__(self, magnitude: float, rjb: float, structure: "Structure") -> None:
        # Required arguments
        self._coefficients = self._coefficient_lookup(structure)
        self._c1 = self._coefficients["c1"]
        self._c2 = self._coefficients["c2"]
        self._c3 = self._coefficients["c3"]
        self._h = self._coefficients["h"]
        self._mref = self._coefficients["mref"]
        self._rref = self._coefficients["rref"]
        self._magnitude = magnitude
        self._rjb = rjb

    def _coefficient_lookup(self) -> Dict:
        return {}
        # implement properly

    def calculate(self) -> float:
        r = np.sqrt((self._rjb**2) + (self._h**2))
        m_term = self._c1 + self._c2 * (self._magnitude - self._mref)
        ln_distance_term = np.log(r / self._rref)
        distance_term = self._c3 * (r - self._rref)
        return (m_term * ln_distance_term) + distance_term


class BSSA13EventTerm(EventTerm):

    def __init__(
        self,
        magnitude: float,
        fault_type: Literal["U", "SS", "NS", "RS"],
        structure: "Structure",
    ) -> None:
        # Requirement arguments
        self._coefficients = self._coefficient_lookup(structure, fault_type)
        self.e0 = self._coefficients("e0")
        self.e1 = self._coefficients("e1")
        self.e2 = self._coefficients("e2")
        self.e3 = self._coefficients("e3")
        self.e4 = self._coefficients("e4")
        self.e5 = self._coefficients("e5")
        self.e6 = self._coefficients("e6")
        self.Mh = self._coefficients("Mh")
        self.fault_type = fault_type
        self.magnitude = magnitude

    def _coefficient_lookup(self) -> Dict:
        return {}
        # implement properly

    def calculate(self) -> float:
        dummy_vars = {
            "U": [1, 0, 0, 0],
            "SS": [0, 1, 0, 0],
            "NS": [0, 0, 1, 0],
            "RS": [0, 0, 0, 1],
        }
        U, SS, NS, RS = dummy_vars[self.fault_type]
        if self.magnitude <= self.Mh:
            return (
                self.e0
                + (self.e1 * SS)
                + (self.e2 * NS)
                + (self.e3 * RS)
                + (self.e4 * (self.magnitude - self.Mh))
                + (self.e5 * ((self.magnitude - self.Mh) ** 2))
            )
        elif self.magnitude > self.Mh:
            return (
                (self.e0 * U)
                + (self.e1 * SS)
                + (self.e2 * NS)
                + (self.e3 * RS)
                + self.e6(self.magnitude - self.Mh)
            )


class BSSA13SiteTerm(SiteTerm):

    def __init__(self, vs30: float | int, pga_r: float, structure: "Structure") -> None:
        self._coefficients = self._coefficient_lookup(structure)
        self._c = self._coefficients["c"]  # type: float
        self._vref = self._coefficients["vref"]  # type: float
        self._vc = self._coefficients["vc"]  # type: float
        self._f1 = self._coefficients["f1"]
        self._f2 = self._coefficients["f2"]
        self._f3 = self._coefficients["f3"]
        self._f2 = self.f2_calculate()
        self._f4 = self._coefficients["f4"]
        self._f5 = self._coefficients["f5"]
        self._vs30 = vs30  # type: float
        self.pga_r = pga_r

    def _coefficient_lookup(self) -> Dict:
        return {}
        # implement properly

    def f2_calculate(self) -> float:
        vs30_exponent = self._f5(min(self._vs30, 760) - 350)
        f5_exponent = self._f5(760 - 360)
        return self._f4(np.e(vs30_exponent) - np.e(f5_exponent))

    def calculate(self, pga_r: float) -> float:
        def _linear_component() -> float:
            if self._vs30 <= self._vc:
                return self._c * np.log((self._vs30 / self._vref))
            elif self._vs30 > self._vc:
                return self._c * np.log((self._vc / self._vref))

        def _nonlinear_component() -> float:
            return self._f1 + (self._f2 * np.log((pga_r + self._f3) / self._f3))

        return _linear_component() + _nonlinear_component
