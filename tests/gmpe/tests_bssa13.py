# std library imports
import unittest

# library imports
import pytest

# module imports
from building.core import Building
from gmpe.bssa13.bssa13 import (
    BSSA13GMPE,
    BSSA13EventTerm,
    BSSA13PathTerm,
    BSSA13SiteTerm,
)


class TestBSSA13GMPEBasicFunctionality(unittest.TestCase):
    """Testing the GMPE's functionality."""

    def setUp(self) -> None:
        building = Building(height=20, lat=100, long=200, period=1, vs30=350)
        self.gmpe = BSSA13GMPE(
            building=building,
            magnitude=5,
            distance=100,
            event_term=BSSA13EventTerm,
            path_term=BSSA13PathTerm,
            site_term=BSSA13SiteTerm,
            fault_type="U",
            coefficients_table="src/gmpe/coefficients/bssa13.json",
            coefficients_list=["c1", "c2", "c3", "c4", "c5"],
        )

    def test_basic_gmpe_instantiation(self) -> None:
        """Test that the GMPE instantiates correctly."""
        self.assertIsInstance(self.gmpe, BSSA13GMPE)

    def test_event_term_coefficients(self) -> None:
        """Test that the EventTerm has the correct coefficient and inherited
        attributes."""
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        event_term = self.gmpe.event_term
        coefficient_keys = ["e0", "e1", "e2", "e3", "e4", "e5", "e6", "Mh"]
        self.assertEqual([i for i in event_term._coefficients.keys()], coefficient_keys)
        expected_coefficient_vals = {
            i: j
            for i, j in zip(
                coefficient_keys,
                [0.3932, 0.4218, 0.207, 0.4124, 1.5004, -0.18983, 0.17895, 6.2],
            )
        }
        self.assertEqual(event_term._e0, expected_coefficient_vals["e0"])
        self.assertEqual(event_term._e1, expected_coefficient_vals["e1"])
        self.assertEqual(event_term._e2, expected_coefficient_vals["e2"])
        self.assertEqual(event_term._e3, expected_coefficient_vals["e3"])
        self.assertEqual(event_term._e4, expected_coefficient_vals["e4"])
        self.assertEqual(event_term._e5, expected_coefficient_vals["e5"])
        self.assertEqual(event_term._e6, expected_coefficient_vals["e6"])
        self.assertEqual(event_term._Mh, expected_coefficient_vals["Mh"])
        self.assertEqual(event_term._magnitude, self.gmpe.magnitude)
        self.assertEqual(event_term._fault_type, self.gmpe.fault_type)

    def test_event_term_calculation(self) -> None:
        """Test the event term calculation result."""
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        self.assertAlmostEqual(self.gmpe.event_term.calculate(), -1.6801552, places=3)
        # BSSA13 provides a piecewise function for M <= Mh and M > Mh, thus we
        # temporarily modify the magnitude of the gmpe.
        self.gmpe._change_attribute("magnitude", 6.3)
        self.assertEqual(self.gmpe.magnitude, 6.3)
        self.assertNotEqual(self.gmpe.magnitude, 5)
        self.assertAlmostEqual(self.gmpe.event_term.calculate(), 0.41105, places=3)
        # revert to mock value of M = 5
        self.gmpe._change_attribute("magnitude", 5)

    def test_path_term_coefficients(self) -> None:
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        """Test that the EventTerm has the correct coefficient and inherited
        attributes."""
        path_term = self.gmpe.path_term
        coefficient_keys = ["c1", "c2", "c3", "mref", "rref", "h"]
        self.assertEqual([i for i in path_term._coefficients.keys()], coefficient_keys)
        expected_coefficient_vals = {
            i: j
            for i, j in zip(
                coefficient_keys,
                [-1.193, 0.10248, -0.00121, 4.5, 1, 5.74],
            )
        }
        self.assertEqual(path_term._c1, expected_coefficient_vals["c1"])
        self.assertEqual(path_term._c2, expected_coefficient_vals["c2"])
        self.assertEqual(path_term._c3, expected_coefficient_vals["c3"])
        self.assertEqual(path_term._mref, expected_coefficient_vals["mref"])
        self.assertEqual(path_term._rref, expected_coefficient_vals["rref"])
        self.assertEqual(path_term._h, expected_coefficient_vals["h"])

    def test_path_term_calculation(self) -> None:
        """Test the event term calculation result."""
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        self.assertAlmostEqual(self.gmpe.path_term.calculate(), -5.379886607, places=3)

    def test_site_term_coefficients(self) -> None:
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        """Test that the SiteTerm has the correct coefficient and inherited
        attributes."""
        site_term = self.gmpe.site_term
        coefficient_keys = ["c", "vc", "vref", "f1", "f3", "f4", "f5"]
        self.assertEqual([i for i in site_term._coefficients.keys()], coefficient_keys)
        expected_coefficient_vals = {
            i: j
            for i, j in zip(
                coefficient_keys,
                [-1.0361, 967.51, 760, 0, 0.1, -0.1052, -0.00844],
            )
        }
        self.assertEqual(site_term._c, expected_coefficient_vals["c"])
        self.assertEqual(site_term._vc, expected_coefficient_vals["vc"])
        self.assertEqual(site_term._vref, expected_coefficient_vals["vref"])
        self.assertEqual(site_term._f1, expected_coefficient_vals["f1"])
        self.assertEqual(site_term._f3, expected_coefficient_vals["f3"])
        self.assertEqual(site_term._f4, expected_coefficient_vals["f4"])
        self.assertEqual(site_term._f5, expected_coefficient_vals["f5"])

    def test_site_term_f2_calculation(self) -> None:
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        self.assertAlmostEqual(self.gmpe.site_term._f2, -0.11087, 3)

    def test_site_term_linear_component_calculation(self) -> None:
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        # for Building, Vs30 < Vc
        self.assertAlmostEqual(self.gmpe.site_term._linear_component, 0.8033766, 3)

    def test_site_term_pga_r_and_nonlinear_component_calculation(self) -> None:
        """Test the calculation of pga in rock and the non-linear component."""
        self.gmpe._calculate_unamplified_pga()
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        # for this calculation, period=0, vs30=760; Rjb=100, M=5
        # coeffecients as follows:
        # event_term = { 'e0': 0.4473, 'e1': 0.4856, 'e2': 0.2459, 'e3': 0.4539,
        # 'e4': 1.431, 'e5': 0.05053, 'e6': -0.1662, 'Mh': 5.5}
        # path_term = {'c1': -1.134, 'c2': 0.1917, 'c3': -0.00809, 'M_ref': 4.5,
        # 'R_ref': 1, 'h_km': 4.5}
        # Site term evaluates to 0 (ln(1))
        self.assertAlmostEqual(self.gmpe.site_term.pga_r, 0.002909, 3)
        # check reversion to original properties:
        self.assertEqual(self.gmpe.magnitude, 5)
        self.assertEqual(self.gmpe.building.period, 1)
        # check the non-linear component, which should evaluate to almost 0 for small pga.
        self.assertAlmostEqual(
            self.gmpe.site_term._calculate_nonlinear_component(), 0.00, 2
        )

    def test_Y_value(self) -> None:
        """Test the final output value."""
        # valid for Building(height=20, lat=100, long=200, period=1, vs30=350)
        self.assertAlmostEqual(self.gmpe.calculate(), -6.2603, 3)


if __name__ == "__main__":
    unittest.main()
