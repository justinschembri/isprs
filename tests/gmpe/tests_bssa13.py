# std library imports
import unittest

# library imports
import pytest

# module imports
from building.core import Building
from gmpe.bssa13.bssa13 import BSSA13GMPE, BSSA13EventTerm, BSSA13PathTerm, BSSA13SiteTerm

class TestGMPEInstantiation(unittest.TestCase):
    def test_basic_gmpe_instantiation(self) -> None:
        building = Building(height=20, lat=100, long=200, period=1, vs30=760)
        gmpe = BSSA13GMPE(
            building=building,
            magnitude=5,
            distance=100,
            event_term=BSSA13EventTerm,
            path_term=BSSA13PathTerm,
            site_term=BSSA13SiteTerm,
            fault_type="U",
            coefficients_table="src/gmpe/bssa13/coefficients.json",
            coefficients_list=['c1', 'c2', 'c3', 'c4', 'c5'],
        )
        self.assertIsInstance(gmpe, BSSA13GMPE)

if __name__ == "__main__":
    unittest.main()