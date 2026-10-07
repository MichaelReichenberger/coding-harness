"""Akzeptanz für Stückmengen im gedruckten Kassenbeleg.

Teller, ShoppingCart und Receipt erzeugen den Beleg; ReceiptPrinter zeigt ihn an.
Stückzahlen werden als ganze Zahlen gedruckt, Gewichte mit drei Nachkommastellen.
Kontrollen prüfen leeren/einzelnen Einkauf und Gewichte. Die übrigen Fälle zeigen
im unveränderten Commit den echten Darstellungsfehler (z. B. 3.0 statt 3).
Dieser geschützte Test ist für das Modell lesbar über seine Ausgabe, nicht editierbar.
"""

import json
import math

from model_objects import ProductUnit
from receipt_printer import ReceiptPrinter
from scenario import checkout


def main():
    # Float-Mengen sind reguläre Eingaben des vorhandenen Warenkorbs.
    # Die Anforderung betrifft die Anzeige, nicht die gespeicherte Menge.
    cases = [
        ("empty", 0.0, ProductUnit.EACH, None),
        ("single", 1.0, ProductUnit.EACH, None),
        ("weight", 1.5, ProductUnit.KILO, "1.500"),
        ("each_2", 2.0, ProductUnit.EACH, "2"),
        ("each_3", 3.0, ProductUnit.EACH, "3"),
        ("each_5", 5.0, ProductUnit.EACH, "5"),
    ]
    controls = {"empty", "single", "weight"}
    report = {
        "positive_control": False,
        "business_failures": [],
        "infrastructure_errors": [],
        "cases": {},
    }
    for name, quantity, unit, expected_quantity in cases:
        try:
            receipt = checkout(quantity, 1.25, offer=None, unit=unit)
            printed = ReceiptPrinter().print_receipt(receipt)
            # Überprüfe die tatsächlich gedruckte Mengenzeile, nicht nur einen
            # isolierten Formatter. So ist die Zusammenarbeit der Module getestet.
            quantity_lines = [line.strip() for line in printed.splitlines() if " * " in line]
            expected_lines = [] if expected_quantity is None else [f"1.25 * {expected_quantity}"]
            passed = (
                quantity_lines == expected_lines
                and math.isclose(receipt.total_price(), quantity * 1.25, abs_tol=1e-9)
                and any(line.strip().startswith("Total:") for line in printed.splitlines())
            )
            report["cases"][name] = {
                "passed": passed,
                "expected": expected_lines,
                "actual": quantity_lines,
            }
            if not passed:
                report["business_failures"].append(name)
            print(
                f"{'PASS' if passed else 'FAIL'} {name}: expected={expected_lines}; actual={quantity_lines}"
            )
        except Exception as exc:
            report["infrastructure_errors"].append(f"{name}: {type(exc).__name__}: {exc}")
    report["positive_control"] = all(
        report["cases"].get(name, {}).get("passed") is True for name in controls
    )
    print("HARNESS_ACCEPTANCE=" + json.dumps(report))
    return (
        0
        if report["positive_control"]
        and not report["business_failures"]
        and not report["infrastructure_errors"]
        else 1
    )
