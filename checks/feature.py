"""S2-F: Geschützte Servicegebühr-Akzeptanz über Kasse und Beleg.

Dieses Modul läuft nur über entry.py im Container. Es enthält Anforderungen,
keinen Patch. Fehlende optionale Argumente sind die erwartete rote Baseline;
fehlende Bibliotheken/Importe dürfen niemals als fachlicher Fehler gelten.
"""

import json
import math
import traceback

from model_objects import Product, ProductUnit, SpecialOfferType
from receipt import Receipt
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def purchase(fee=None, *, provided=True, discount=False):
    product = Product("bread", ProductUnit.EACH)
    catalog = FakeCatalog()
    catalog.add_product(product, 2.0)
    cart = ShoppingCart()
    cart.add_item_quantity(product, 2)
    teller = Teller(catalog)
    if discount:
        teller.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, product, 10.0)
    return (
        teller.checks_out_articles_from(cart, service_fee=fee)
        if provided
        else teller.checks_out_articles_from(cart)
    )


def main():
    failures, errors, cases = [], [], {}

    def case(name, operation):
        try:
            passed = bool(operation())
        except (TypeError, ValueError, AttributeError, OverflowError) as exc:
            # API fehlt oder fachlicher Pfad ist noch nicht implementiert.
            passed = False
            print(f"{name}: {type(exc).__name__}: {exc}")
            traceback.print_exc(limit=-3)
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            passed = False
        cases[name] = passed
        if not passed:
            failures.append(name)
        print(f"{'PASS' if passed else 'FAIL'} {name}")

    case("legacy", lambda: math.isclose(purchase(provided=False).total_price(), 4.0))
    case("legacy_receipt", lambda: Receipt().total_price() == 0)
    case("fee_checkout", lambda: math.isclose(purchase(1.5).total_price(), 5.5))
    case("fee_receipt", lambda: math.isclose(Receipt(service_fee=1.5).total_price(), 1.5))
    case("fee_zero", lambda: math.isclose(purchase(0).total_price(), 4.0))
    case("fee_with_discount", lambda: math.isclose(purchase(1.5, discount=True).total_price(), 5.1))

    # Der Warenzwischensaldo muss auch neben sehr grossen Gebuehren erhalten bleiben.
    def preserves_subtotal(fee, discount):
        expected = purchase(0, discount=discount).total_price()
        actual = purchase(fee, discount=discount).total_price() - fee
        print(f"subtotal expected={expected!r} actual={actual!r}")
        return math.isclose(actual, expected)

    for exponent in (30, 400):
        fee = 10**exponent
        case(
            f"large_fee_receipt_{exponent}",
            lambda fee=fee: Receipt(service_fee=fee).total_price() == fee,
        )
        for discount in (False, True):
            case(
                f"large_fee_checkout_{exponent}_{discount}",
                lambda fee=fee, discount=discount: preserves_subtotal(fee, discount),
            )

    def invalid(value, direct):
        try:
            Receipt(service_fee=value) if direct else purchase(value)
        except ValueError as exc:
            return bool(str(exc).strip())
        return False

    for index, value in enumerate(
        (-1, float("nan"), float("inf"), "1.5", None, True, False, -float("inf"), -(10**400))
    ):
        for direct in (False, True):
            case(f"invalid_{index}_{direct}", lambda v=value, d=direct: invalid(v, d))
    evidence = {
        "positive_control": cases["legacy"] and cases["legacy_receipt"],
        "feature_failures": failures,
        "infrastructure_errors": errors,
        "cases": cases,
    }
    print("HARNESS_FEATURE=" + json.dumps(evidence))
    return 1 if failures or errors else 0
