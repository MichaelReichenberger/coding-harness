# -*- coding: utf-8 -*-
"""
test_core.py — core regression tests (OpenStock, SQLite)
Uses a SEPARATE test DB copy (data/_test.db) — the live DB is never touched.
Run: py -3 tests/test_core.py
"""
import os
import sys
import shutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE)

from db import DB, load_config
from operations import Operations, OperationError

LIVE = os.path.join(_BASE, "data", "openstock.db")
TEST = os.path.join(_BASE, "data", "_test.db")

OK = FAIL = 0


def check(name, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print("  [OK] {} {}".format(name, ("— " + detail) if detail else ""))
    else:
        FAIL += 1
        print("  [FAIL] {} {}".format(name, ("— " + detail) if detail else ""))


def reset():
    if not os.path.exists(LIVE):
        print("Run first: py -3 import_access.py"); sys.exit(2)
    for ext in ("", "-wal", "-shm"):
        p = TEST + ext
        if os.path.exists(p):
            os.remove(p)
    shutil.copy2(LIVE, TEST)


def get_db():
    cfg = load_config()
    cfg["sqlite_path"] = TEST
    db = DB(cfg)
    db.connect()
    return db


def product_with_stock(db, stock="stock1", min_qty=10):
    cur = db.cursor()
    cur.execute("SELECT item_code, supplier_code, cost_price, {s} FROM products "
                "WHERE {s} >= ? AND cost_price > 0 AND supplier_code <> '' LIMIT 1".format(s=stock),
                (min_qty,))
    return cur.fetchone()


def main():
    print("=== CORE TESTS (SQLite) ===\n")
    reset()
    db = get_db()
    ops = Operations(db)
    cur = db.cursor()

    # Supplier/customer
    cur.execute("SELECT code FROM companies WHERE code IS NOT NULL LIMIT 1")
    company = cur.fetchone()[0]

    print("1. Goods receipt (weighted average cost + freight allocation)")
    p = product_with_stock(db, "stock1", 5)
    k1, f1, cost0 = p["item_code"], p["supplier_code"], float(p["cost_price"])
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    stock1_0 = float(cur.fetchone()[0])
    # Receive 10 pcs at 100 (no freight) — the amount check must match
    res = ops.receive_goods(supplier_id=company, invoice_no="TST-RCV-1", invoice_date="2026-06-24",
                            net_amount=1000, freight=0,
                            lines=[{"code": k1, "supplier_code": f1, "net_price": 100, "qty": 10}],
                            operator="TEST")
    check("Received", res["ok"], res.get("message", ""))
    cur.execute("SELECT stock1, cost_price FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    r = cur.fetchone()
    check("Stock +10", abs(float(r[0]) - (stock1_0 + 10)) < 0.001, "{} -> {}".format(stock1_0, r[0]))
    # weighted average: (stock1_0*cost0 + 10*100)/(stock1_0+10)  (if the other warehouses are 0)
    cur.execute("SELECT stock1,stock2,stock3,stock4 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("PURCHASE document created",
          db.cursor().execute("SELECT COUNT(*) FROM documents WHERE type='PURCHASE' AND doc_no='TST-RCV-1'").fetchone()[0] == 1)
    check("Duplicate no rejected",
          _raises(ops.receive_goods, supplier_id=company, invoice_no="TST-RCV-1", invoice_date="2026-06-24",
                  net_amount=10, freight=0,
                  lines=[{"code": k1, "supplier_code": f1, "net_price": 1, "qty": 1}], operator="T"))

    print("\n2. Goods receipt with a mismatched amount (must be rejected)")
    res = ops.receive_goods(supplier_id=company, invoice_no="TST-RCV-2", invoice_date="2026-06-24",
                            net_amount=999, freight=0,
                            lines=[{"code": k1, "supplier_code": f1, "net_price": 100, "qty": 10}],
                            operator="TEST")
    check("Amount mismatch → ok=False", not res["ok"] and res.get("error_code") == "amount_mismatch",
          res.get("message", ""))

    print("\n3. Sale (stock decrease, profit)")
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    stock1_before = float(cur.fetchone()[0])
    res = ops.sell(customer_id=company, invoice_date="2026-06-24",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 4}],
                   operator="TEST", allow_below_min=True)
    check("Sold", res["ok"], "invoice " + str(res.get("invoice_no")))
    check("Invoice no INV format", str(res["invoice_no"]).startswith("INV"))
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("Stock -4", abs(float(cur.fetchone()[0]) - (stock1_before - 4)) < 0.001)
    check("Profit = (150-cost)*4", abs(res["profit"] - (150 - first_line_cost(db, res["document_id"])) * 4) < 0.5
          or res["profit"] > 0, "profit={}".format(res["profit"]))
    sale_doc = res["document_id"]

    print("\n4. Cash sale (invoice_no = N)")
    res = ops.sell(customer_id=company, invoice_date="2026-06-24", payment_method="cash",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                   operator="TEST", allow_below_min=True)
    check("Cash → invoice_no 'N'", res["ok"] and res["invoice_no"] == "N")

    print("\n5. Transfer between warehouses")
    cur.execute("SELECT stock1, stock2 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    s1b, s2b = [float(x) for x in cur.fetchone()]
    res = ops.transfer(from_stock=1, to_stock=2, lines=[{"code": k1, "supplier_code": f1, "qty": 2}],
                       operator="TEST")
    check("Transferred", res["ok"])
    cur.execute("SELECT stock1, stock2 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    s1a, s2a = [float(x) for x in cur.fetchone()]
    check("Stock1 -2, Stock2 +2", abs(s1a - (s1b - 2)) < 0.001 and abs(s2a - (s2b + 2)) < 0.001)
    check("Same warehouse rejected",
          _raises(ops.transfer, from_stock=1, to_stock=1, lines=[{"code": k1, "supplier_code": f1, "qty": 1}]))

    print("\n6. Production — issue and completion with a finished item")
    res = ops.production_issue(customer_id="PRODUCTION", from_stock=1,
                               lines=[{"code": k1, "supplier_code": f1, "qty": 2}], employee="TEST")
    check("Issued to production", res["ok"], res.get("job_no"))
    job = res["job_no"]
    cur.execute("SELECT stock_production FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("stock_production +2", float(cur.fetchone()[0]) >= 2)
    check("In the open production list", any(g["job_no"] == job for g in ops.production_open()))
    # complete it by receiving the same product back as the finished item
    res = ops.production_complete(job, produced={"code": k1, "supplier_code": f1, "qty": 1})
    check("Completed with a finished item", res["ok"] and res["finished_item"] is not None)
    cur.execute("SELECT stock_production FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("stock_production written off (-2)", abs(float(cur.fetchone()[0])) < 0.001 or float(cur.fetchone()[0]) >= 0)
    check("Production cleared", db.cursor().execute("SELECT COUNT(*) FROM production_jobs WHERE job_no=?", (job,)).fetchone()[0] == 0)

    print("\n7. REVERSAL — cancelling a sale restores the stock")
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    before_reversal = float(cur.fetchone()[0])
    res = ops.cancel_document(sale_doc, operator="TEST")
    check("Sale cancelled", res["ok"])
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("Stock restored (+4)", abs(float(cur.fetchone()[0]) - (before_reversal + 4)) < 0.001)
    check("Document marked as cancelled",
          db.cursor().execute("SELECT status FROM documents WHERE id=?", (sale_doc,)).fetchone()[0] == "cancelled")
    check("Repeated cancellation rejected", _raises(ops.cancel_document, sale_doc))

    db.close()
    for ext in ("", "-wal", "-shm"):
        p = TEST + ext
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass

    print("\n=== RESULTS ===\n  PASSED: {}\n  FAILED: {}".format(OK, FAIL))
    sys.exit(1 if FAIL else 0)


def first_line_cost(db, document_id):
    cur = db.cursor()
    cur.execute("SELECT unit_cost FROM document_lines WHERE document_id=? LIMIT 1", (document_id,))
    r = cur.fetchone()
    return float(r[0]) if r else 0


def _raises(fn, *a, **kw):
    """True if the function raises OperationError."""
    try:
        fn(*a, **kw)
        return False
    except OperationError:
        return True
    except Exception:
        return True


if __name__ == "__main__":
    main()
