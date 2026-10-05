"""Authenticated transfer contract across app -> operations -> SQLite.

Not collected by the host pytest suite. All data and credentials are synthetic.
"""
import json
import sqlite3


def main():
    import app as target

    conn = target.DB_.conn
    template = sqlite3.connect(":memory:")
    conn.backup(template)
    cases = [("positive", [2]), ("negative", [-1]), ("zero", [0]),
             ("mixed", [2, -1]), ("mixed_zero", [2, 0])]
    report = {"positive_control": False, "business_failures": [], "infrastructure_errors": [],
              "cases": {}}

    def snapshot():
        return {
            "stock": [tuple(row) for row in conn.execute(
                "SELECT id,stock1,stock2,stock3,stock4,stock_production FROM products ORDER BY id")],
            "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "lines": conn.execute("SELECT COUNT(*) FROM document_lines").fetchone()[0],
        }

    for name, quantities in cases:
        try:
            template.backup(conn)
            client = target.app.test_client()
            login = client.post("/api/operator/login", json={"username": "harness", "password": "synthetic-test-only"})
            assert login.status_code == 200 and login.json.get("session_id"), "Authentifizierung fehlgeschlagen"
            headers = {"X-Session-Id": login.json["session_id"]}
            before = snapshot()
            lines = [{"code": code, "supplier_code": "SUP01", "qty": qty}
                     for code, qty in zip(["BOLT-M8-30", "NUT-M8"], quantities)]
            response = client.post("/api/transfer", headers=headers,
                                   json={"from_stock": 1, "to_stock": 2, "lines": lines})
            after = snapshot()
            if response.status_code not in {200, 400}:
                raise RuntimeError(f"Unerwarteter HTTP-Status {response.status_code}: {response.json}")
            if name == "positive":
                product = conn.execute("SELECT stock1,stock2 FROM products WHERE item_code='BOLT-M8-30'").fetchone()
                passed = (response.status_code == 200 and response.json.get("ok") is True
                          and tuple(product) == (3998, 502)
                          and after["documents"] == before["documents"] + 1
                          and after["lines"] == before["lines"] + 1)
                report["positive_control"] = passed
                if not passed:
                    report["infrastructure_errors"].append("Positivkontrolle fehlgeschlagen")
            else:
                error = str((response.json or {}).get("error", "")).lower()
                meaningful = (any(word in error for word in ("quantity", "qty", "menge"))
                              and any(word in error for word in ("positive", "> 0", "greater", "größer", "zero", "null")))
                passed = (response.status_code == 400 and meaningful and before == after)
                if not passed:
                    report["business_failures"].append(name)
            report["cases"][name] = {"passed": passed, "http": response.status_code,
                                      "body": response.json, "unchanged": before == after,
                                      "documents_before": before["documents"],
                                      "documents_after": after["documents"]}
            print(f"{'PASS' if passed else 'FAIL'} {name}: HTTP {response.status_code}; unchanged={before == after}")
        except Exception as exc:
            report["infrastructure_errors"].append(f"{name}: {exc}")
    template.close()
    target.DB_.close()
    print("HARNESS_ACCEPTANCE=" + json.dumps(report, ensure_ascii=False))
    return 0 if report["positive_control"] and not report["business_failures"] and not report["infrastructure_errors"] else 1
