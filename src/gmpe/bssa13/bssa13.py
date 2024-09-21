# stdlib imports
from pathlib import Path
import numpy as np
from typing import Dict, List, Literal, Type, Optional
import copy

# external imports

# internal imports
from src.gmpe.core import GMPE, PathTerm, EventTerm, SiteTerm
from src.building.core import Building


class BSSA13GMPE(GMPE):
    def __init__(
        self,
        building: Building,
        magnitude: float,
        distance: float,
        event_term: "BSSA13EventTerm",
        path_term: "BSSA13PathTerm",
        site_term: "BSSA13SiteTerm",
        fault_type: None | Literal["U"] | Literal["SS"] | Literal["NS"] | Literal["RS"],
        coefficients_table: Path,
        coefficients_list: List[str],
    ) -> None:
        super().__init__(
            building,
            magnitude,
            distance,
            event_term,
            path_term,
            site_term,
            fault_type,
            coefficients_table,
            coefficients_list,
        )

    def _calculate_unamplified_pga(self):
        actual_building = copy.copy(self.building)
        self._change_attribute("building", self.building.ground())
        pga_r = np.exp(
            self.event_term.calculate()
            + self.path_term.calculate()
            + self.site_term._linear_component
        )
        # revert back to original building:
        self._change_attribute("building", actual_building)
        self.site_term.set_pga_r(pga_r)

        # TODO: #17 Messy implementation.

    def calculate(self) -> float:
        self._calculate_unamplified_pga()

        return (
            self.event_term.calculate()
            + self.path_term.calculate()
            + self.site_term.calculate()
        )


class BSSA13PathTerm(PathTerm):
    def __init__(
        self,
        coefficients_table: Path,
        coefficients_list: List[str],
        building: Building,
        magnitude: float,
        distance: float,
    ) -> None:
        super().__init__(
            coefficients_table, coefficients_list, building, magnitude, distance
        )
        # Required arguments
        coefficient_keys = ["c1", "c2", "c3", "mref", "rref", "h"]
        self._coefficients = self._coefficients_lookup(
            [(i, self.building.period) for i in coefficient_keys]
        )
        self._c1 = self._coefficients["c1"]
        self._c2 = self._coefficients["c2"]
        self._c3 = self._coefficients["c3"]
        self._mref = self._coefficients["mref"]
        self._rref = self._coefficients["rref"]
        self._h = self._coefficients["h"]
        self._magnitude = magnitude
        self._rjb = distance

    def calculate(self) -> float:
        r = np.sqrt((self._rjb**2) + (self._h**2))
        m_term = self._c1 + self._c2 * (self._magnitude - self._mref)
        ln_distance_term = np.log(r / self._rref)
        distance_term = self._c3 * (r - self._rref)
        return (m_term * ln_distance_term) + distance_term


class BSSA13EventTerm(EventTerm):

    def __init__(
        self,
        coefficients_table: Path,
        coefficients_list: List[str],
        magnitude: float,
        building: Building,
        fault_type: Literal["U"] | Literal["SS"] | Literal["NS"] | Literal["RS"],
    ) -> None:
        super().__init__(coefficients_table, coefficients_list, building, magnitude)
        self._fault_type = fault_type
        # Requirement arguments
        coefficient_keys = ["e0", "e1", "e2", "e3", "e4", "e5", "e6", "Mh"]
        self._coefficients = self._coefficients_lookup(
            [(i, self.building.period) for i in coefficient_keys]
        )
        self._e0 = self._coefficients["e0"]
        self._e1 = self._coefficients["e1"]
        self._e2 = self._coefficients["e2"]
        self._e3 = self._coefficients["e3"]
        self._e4 = self._coefficients["e4"]
        self._e5 = self._coefficients["e5"]
        self._e6 = self._coefficients["e6"]
        self._Mh = self._coefficients["Mh"]
        self._fault_type = fault_type
        self._magnitude = magnitude

    def calculate(self) -> float:
        dummy_vars = {
            "U": [1, 0, 0, 0],
            "SS": [0, 1, 0, 0],
            "NS": [0, 0, 1, 0],
            "RS": [0, 0, 0, 1],
        }
        U, SS, NS, RS = dummy_vars[self._fault_type]
        if self._magnitude <= self._Mh:
            return (
                self._e0
                + (self._e1 * SS)
                + (self._e2 * NS)
                + (self._e3 * RS)
                + (self._e4 * (self._magnitude - self._Mh))
                + (self._e5 * ((self._magnitude - self._Mh) ** 2))
            )
        elif self._magnitude > self._Mh:
            return (
                (self._e0 * U)
                + (self._e1 * SS)
                + (self._e2 * NS)
                + (self._e3 * RS)
                + self._e6 * (self._magnitude - self._Mh)
            )


class BSSA13SiteTerm(SiteTerm):

    def __init__(
        self,
        coefficient_table: Path,
        coefficients_list: List[str],
        vs30: float,
        building: Building,
        pga_r: float | None = None,
    ) -> None:
        super().__init__(
            coefficient_table=coefficient_table,
            coefficients_list=coefficients_list,
            vs30=vs30,
            pga_r=pga_r,
            building=building,
        )
        # TODO: #16 This could be a class attribute:
        coefficient_keys = ["c", "vc", "vref", "f1", "f3", "f4", "f5"]
        self._coefficients = self._coefficients_lookup(
            [(i, self.building.period) for i in coefficient_keys]
        )
        self._c = self._coefficients["c"]  # type: float
        self._vc = self._coefficients["vc"]  # type: float
        self._vref = self._coefficients["vref"]  # type: float
        self._f1 = self._coefficients["f1"]
        self._f3 = self._coefficients["f3"]
        self._f4 = self._coefficients["f4"]
        self._f5 = self._coefficients["f5"]
        self._vs30 = vs30  # type: float
        self.pga_r = None
        self._f2 = self.f2_calculate()
        self._linear_component = self._calculate_linear_component()

    def set_pga_r(self, pga_r: float) -> None:
        setattr(self, "pga_r", pga_r)

    def f2_calculate(self) -> float:
        vs30_exponent = self._f5 * (min(self._vs30, 760) - 360)
        f5_exponent = self._f5 * (760 - 360)
        return self._f4 * (np.exp(vs30_exponent) - np.exp(f5_exponent))

    def _calculate_linear_component(self) -> float:
        if self._vs30 <= self._vc:
            return self._c * np.log((self._vs30 / self._vref))
        elif self._vs30 > self._vc:
            return self._c * np.log((self._vc / self._vref))
        

    def _calculate_nonlinear_component(self) -> float:
        return self._f1 + (self._f2 * np.log((self.pga_r + self._f3) / self._f3))
    
    
    def calculate(self) -> float:
        return self._linear_component + self._calculate_nonlinear_component()
