"""Testaufbau mit synthetischem Katalog und echten Anwendungsmodulen.

FakeCatalog ersetzt nur die Speicherung der Preise. Warenkorb, Kasse, Produkte,
Rabattlogik und Beleg werden aus dem zu prüfenden Repository importiert.
"""

from model_objects import Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def checkout(
    quantity, price=1.0, offer=SpecialOfferType.TWO_FOR_AMOUNT, argument=1.5, unit=ProductUnit.EACH
):
    """Erzeugt pro Aufruf frische Daten und führt den gesamten Kassiervorgang aus."""
    catalog = FakeCatalog()
    product = Product("synthetic product", unit)
    catalog.add_product(product, price)
    teller = Teller(catalog)
    if offer is not None:
        teller.add_special_offer(offer, product, argument)
    cart = ShoppingCart()
    if quantity:
        cart.add_item_quantity(product, quantity)
    return teller.checks_out_articles_from(cart)
