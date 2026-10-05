"""Synthetic catalog; the cart, teller, products and receipt come from the target."""
from model_objects import Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def checkout(quantity, price=1.0, offer=SpecialOfferType.TWO_FOR_AMOUNT, argument=1.5, unit=ProductUnit.EACH):
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
