# # standard library imports:
# from unittest import TestCase

# # library imports

# # internal imports
# from src.building.core import ASCEBuilding


# class TestASCEBuildings(TestCase):
#     """Test the ASCE building building subclass."""
#     def setUp(self) -> None:
#         self.building = ASCEBuilding(height=15, 
#                                 lat=100, 
#                                 long=100, 
#                                 vs30=350, 
#                                 coefficients_table="src/building/coefficients/asce7-10.json", 
#                                 structure_type="Steel MRF",
#                                 period=None)
    
#     def test_natural_periods(self) -> None:
#         """Test calculation of natural period using ASCE methodology."""
#         self.assertAlmostEqual(self.building._calculate_natural_period(), 0.631846, 4)
#         self.assertAlmostEqual(self.building.period, 0.631846, 4)