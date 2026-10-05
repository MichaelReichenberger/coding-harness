"""Pair-offer behavior across Teller -> ShoppingCart -> Receipt, only in Docker."""
import json
import math

from scenario import checkout


def main():
    cases = [
        ("empty", 0, 1.0, 1.5, 0.0),
        ("single", 1, 1.0, 1.5, 1.0),
        ("pair", 2, 1.0, 1.5, 1.5),
        ("two_pairs", 4, 1.0, 1.5, 3.0),
        ("odd_3", 3, 1.0, 1.5, 2.5),
        ("odd_5", 5, 2.0, 3.0, 8.0),
        ("odd_7", 7, 0.99, 1.5, 5.49),
    ]
    controls = {"empty", "single", "pair", "two_pairs"}
    report = {"positive_control": False, "business_failures": [], "infrastructure_errors": [], "cases": {}}
    for name, quantity, price, bundle, expected in cases:
        try:
            receipt = checkout(quantity, price, argument=bundle)
            actual = receipt.total_price()
            passed = (math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9)
                      and len(receipt.items) == (1 if quantity else 0)
                      and (not quantity or receipt.items[0].quantity == quantity)
                      and len(receipt.discounts) == (1 if quantity >= 2 else 0))
            report["cases"][name] = {"passed": passed, "quantity": quantity,
                "unit_price": price, "pair_price": bundle, "expected": expected, "actual": actual}
            if not passed:
                report["business_failures"].append(name)
            print(f"{'PASS' if passed else 'FAIL'} {name}: expected={expected:.2f}; actual={actual:.2f}")
        except Exception as exc:
            report["infrastructure_errors"].append(f"{name}: {type(exc).__name__}: {exc}")
    report["positive_control"] = all(report["cases"].get(name, {}).get("passed") is True for name in controls)
    print("HARNESS_ACCEPTANCE=" + json.dumps(report))
    return 0 if report["positive_control"] and not report["business_failures"] and not report["infrastructure_errors"] else 1
