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


class TestGMPE(unittest.TestCase):
    """Testing the GMPE's functionality."""

    def setUp(self) -> None:
        building = Building(height=20, lat=100, long=200, period=1, vs30=760)
        self.gmpe = BSSA13GMPE(
            building=building,
            magnitude=5,
            distance=100,
            event_term=BSSA13EventTerm,
            path_term=BSSA13PathTerm,
            site_term=BSSA13SiteTerm,
            fault_type="U",
            coefficients_table="src/gmpe/bssa13/coefficients.json",
            coefficients_list=["c1", "c2", "c3", "c4", "c5"],
        )

    def test_basic_gmpe_instantiation(self) -> None:
        """Test that the GMPE instantiates correctly."""
        self.assertIsInstance(self.gmpe, BSSA13GMPE)

    def test_event_term_coefficients(self) -> None:
        """Test that the PathTerm has the correct coefficient and inherited attributes."""
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
        self.assertEqual(event_term.e0, expected_coefficient_vals["e0"])
        self.assertEqual(event_term.e1, expected_coefficient_vals["e1"])
        self.assertEqual(event_term.e2, expected_coefficient_vals["e2"])
        self.assertEqual(event_term.e3, expected_coefficient_vals["e3"])
        self.assertEqual(event_term.e4, expected_coefficient_vals["e4"])
        self.assertEqual(event_term.e5, expected_coefficient_vals["e5"])
        self.assertEqual(event_term.e6, expected_coefficient_vals["e6"])
        self.assertEqual(event_term.Mh, expected_coefficient_vals["Mh"])
        self.assertEqual(event_term.magnitude, 5)
        self.assertEqual(event_term.fault_type, "U")
    
    def test_event_term_calculation(self) -> None:
        """Test the event term calculation result."""
        self.assertAlmostEqual(self.gmpe.event_term.calculate(), -1.6801552, places=3)

if __name__ == "__main__":
    unittest.main()
