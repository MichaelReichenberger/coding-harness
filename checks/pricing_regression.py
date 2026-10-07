"""Zusätzliche Preisregeln, vor und nach jeder Änderung identisch geprüft."""

import unittest

from model_objects import ProductUnit, SpecialOfferType
from scenario import checkout


class PricingRegression(unittest.TestCase):
    """Schützt Normal-/Gewichtspreise und andere Angebote vor Nebenwirkungen."""

    def test_no_offer(self):
        self.assertAlmostEqual(checkout(3, 1.25, offer=None).total_price(), 3.75)

    def test_weighted_product(self):
        self.assertAlmostEqual(
            checkout(2.5, 1.99, offer=None, unit=ProductUnit.KILO).total_price(), 4.975
        )

    def test_percentage_discount(self):
        self.assertAlmostEqual(
            checkout(
                3, 2.0, offer=SpecialOfferType.TEN_PERCENT_DISCOUNT, argument=10.0
            ).total_price(),
            5.4,
        )

    def test_three_for_two(self):
        self.assertAlmostEqual(
            checkout(7, 1.0, offer=SpecialOfferType.THREE_FOR_TWO, argument=0).total_price(), 5.0
        )

    def test_five_for_amount(self):
        self.assertAlmostEqual(
            checkout(6, 1.0, offer=SpecialOfferType.FIVE_FOR_AMOUNT, argument=4.0).total_price(),
            5.0,
        )
