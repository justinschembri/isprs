"""Tests for the building module."""

# standard library imports:
from unittest import TestCase

# library imports:
# package imports:

from src.building.core import Building, SeismicProperties, calculate_asce_period


class TestCore(TestCase):
    """Tests for the core module."""

    def setUp(self) -> None:
        seismic_properties = SeismicProperties(
            period_function=calculate_asce_period,
            height=10,
            structure_type="Steel MRF",
            vs30=760,
        )
        ground_properties = SeismicProperties(
            period=0, height=10, structure_type="Steel MRF", vs30=760
        )
        self.building = Building(
            latitude=100, longitude=100, seismic_properties=seismic_properties
        )

        self.ground = Building(
            latitude=100, longitude=100, seismic_properties=ground_properties
        )

    def test_period_calculation(self) -> None:
        """Test the base building class."""
        self.assertAlmostEqual(self.building.seismic_properties.period, 0.4568, 3)

    def test_ground(self) -> None:
        """Test the 'ground' object built into the Building Class."""
        self.assertEqual(self.building.ground().latitude, self.ground.latitude)
        self.assertEqual(self.building.ground().longitude, self.ground.longitude)
        self.assertEqual(
            self.building.ground().seismic_properties.properties["vs30"],
            self.ground.seismic_properties.properties["vs30"],
        )
        self.assertEqual(
            self.building.ground().seismic_properties.properties["height"],
            self.ground.seismic_properties.properties["height"],
        )
