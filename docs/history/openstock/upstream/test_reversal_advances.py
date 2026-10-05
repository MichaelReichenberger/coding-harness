# -*- coding: utf-8 -*-
"""
test_reversal_advances.py — regression tests for the new logic (OpenStock, SQLite):
  1) A REVERSAL returns the consumed advance to the customer (the balance is restored).
  2) Ownership check: without admin/all_documents you may cancel ONLY your own document.
  3) due_date is calculated for credit (transfer) sales from the customer's payment terms.
Uses a SEPARATE test DB copy (data/_test_reversal.db) — the live DB is never touched.
Run: py -3 tests/test_reversal_advances.py
"""
import os
import sys
import shutil
import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE)

from db import DB, load_config
from operations import Operations, OperationError

LIVE = os.path.join(_BASE, "data", "openstock.db")
TEST = os.path.join(_BASE, "data", "_test_reversal.db")

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
    db.apply_migrations()   # apply pending migrations to the copy (e.g. 008 document_id)
    return db


def product_with_stock(db, stock="stock1", min_qty=10):
    cur = db.cursor()
    cur.execute("SELECT item_code, supplier_code, cost_price, {s} FROM products "
                "WHERE {s} >= ? AND cost_price > 0 AND supplier_code <> '' LIMIT 1".format(s=stock),
                (min_qty,))
    return cur.fetchone()


def _raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
        return False
    except OperationError:
        return True


def main():
    print("=== REVERSAL + ADVANCE + OWNERSHIP (SQLite) ===\n")
    reset()
    db = get_db()
    ops = Operations(db)
    cur = db.cursor()

    cur.execute("SELECT code FROM companies WHERE code IS NOT NULL LIMIT 1")
    customer = cur.fetchone()[0]
    p = product_with_stock(db, "stock1", 20)
    if not p:
        print("No product with enough stock — test skipped."); sys.exit(2)
    k1, f1 = p["item_code"], p["supplier_code"]

    # ─────────────────────────────────────────────────────────────
    print("1. A REVERSAL returns the consumed advance")
    bal0 = db.get_advance_balance(customer)
    db.register_advance(customer, 1000, operator="TEST")
    check("Advance +1000", abs(db.get_advance_balance(customer) - (bal0 + 1000)) < 0.001,
          "{} -> {}".format(bal0, db.get_advance_balance(customer)))

    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    stock_before = float(cur.fetchone()[0])
    res = ops.sell(customer_id=customer, invoice_date="2026-07-18", payment_method="transfer",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 3}],
                   operator="OWNER1", allow_below_min=True)
    check("Sold", res["ok"], "invoice " + str(res.get("invoice_no")))
    document_id = res["document_id"]; invoice_no = res["invoice_no"]; debt = res["customer_debt"]

    # Consume the advance (the way app.py does after a sale — with document_id)
    used = db.use_advance(customer, debt, doc_no=invoice_no, operator="OWNER1",
                          document_id=document_id)
    bal_after_sale = db.get_advance_balance(customer)
    check("Advance consumed (balance -{:.2f})".format(used),
          abs(bal_after_sale - (bal0 + 1000 - used)) < 0.001,
          "used={} balance={}".format(used, bal_after_sale))
    check("Consumed > 0", used > 0, "used={}".format(used))

    # Cancel (as admin) — must return both the advance AND the stock
    res_a = ops.cancel_document(document_id, operator="ADMIN9", permissions=["admin"])
    check("Cancelled", res_a["ok"])
    check("Refunded advance == consumed",
          abs(res_a.get("advance_refunded", 0) - used) < 0.001,
          "refunded={} used={}".format(res_a.get("advance_refunded"), used))
    bal_after_reversal = db.get_advance_balance(customer)
    check("Advance balance restored",
          abs(bal_after_reversal - (bal0 + 1000)) < 0.001,
          "{} (should be {})".format(bal_after_reversal, bal0 + 1000))
    cur.execute("SELECT stock1 FROM products WHERE item_code=? AND supplier_code=?", (k1, f1))
    check("Warehouse stock restored (+3)",
          abs(float(cur.fetchone()[0]) - stock_before) < 0.001)
    check("Repeated cancellation rejected",
          _raises(ops.cancel_document, document_id, operator="ADMIN9", permissions=["admin"]))

    # ─────────────────────────────────────────────────────────────
    print("\n2. Ownership check (only the owner / admin / all_documents may cancel)")
    res = ops.sell(customer_id=customer, invoice_date="2026-07-18", payment_method="transfer",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 2}],
                   operator="OWNER1", allow_below_min=True)
    doc2 = res["document_id"]
    check("SOMEONE ELSE'S without the permission — blocked",
          _raises(ops.cancel_document, doc2, operator="OTHER2", permissions=["sell", "read"]))
    # The document is still active after the blocked attempt
    cur.execute("SELECT status FROM documents WHERE id=?", (doc2,))
    check("Document stayed active after the blocked attempt", cur.fetchone()[0] == "active")
    # the all_documents permission — allows cancelling someone else's
    res_v = ops.cancel_document(doc2, operator="OTHER2", permissions=["sell", "all_documents"])
    check("With 'all_documents' — allowed", res_v["ok"])

    # The owner cancels their own — allowed
    res = ops.sell(customer_id=customer, invoice_date="2026-07-18", payment_method="transfer",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                   operator="OWNER1", allow_below_min=True)
    doc3 = res["document_id"]
    res_o = ops.cancel_document(doc3, operator="OWNER1", permissions=["sell"])
    check("The owner cancels their own — allowed", res_o["ok"])

    # ─────────────────────────────────────────────────────────────
    print("\n3. due_date for a credit sale from the customer's payment terms")
    db.cursor().execute("UPDATE companies SET payment_terms_days=14 WHERE code=?", (customer,))
    db.conn.commit()
    res = ops.sell(customer_id=customer, invoice_date="2026-07-01", payment_method="transfer",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                   operator="OWNER1", allow_below_min=True)
    cur.execute("SELECT due_date FROM documents WHERE id=?", (res["document_id"],))
    due = (cur.fetchone()[0] or "")[:10]
    expected = (datetime.date(2026, 7, 1) + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
    check("due_date = date + payment terms", due == expected, "{} (should be {})".format(due, expected))

    # Cash — no due_date
    res = ops.sell(customer_id=customer, invoice_date="2026-07-01", payment_method="cash",
                   lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                   operator="OWNER1", allow_below_min=True)
    cur.execute("SELECT due_date FROM documents WHERE id=?", (res["document_id"],))
    check("Cash — due_date empty", not (cur.fetchone()[0] or ""))

    # ─────────────────────────────────────────────────────────────
    print("\n4. Advance collision across cash sales (shared doc_no 'N') — refunds ONLY its own")
    b0 = db.get_advance_balance(customer)
    if b0 < 400:
        db.register_advance(customer, 400, operator="TEST")
        b0 = db.get_advance_balance(customer)

    def cash_sale():
        r = ops.sell(customer_id=customer, invoice_date="2026-07-18", payment_method="cash",
                     lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                     operator="OWNER1", allow_below_min=True)
        used = db.use_advance(customer, r["customer_debt"], doc_no=r["invoice_no"],
                              operator="OWNER1", document_id=r["document_id"])
        return r["document_id"], used

    docA, usedA = cash_sale()
    docB, usedB = cash_sale()
    check("Both cash sales (N) consumed an advance", usedA > 0 and usedB > 0,
          "A={} B={}".format(usedA, usedB))
    check("Balance decreased by usedA+usedB",
          abs(db.get_advance_balance(customer) - (b0 - usedA - usedB)) < 0.001)

    # Cancel ONLY A — MUST refund only usedA (the old bug refunded usedA+usedB)
    resA = ops.cancel_document(docA, operator="ADMIN9", permissions=["admin"])
    check("Reversal of A refunded ONLY usedA (not usedA+usedB)",
          abs(resA["advance_refunded"] - usedA) < 0.001,
          "refunded={} usedA={} usedB={}".format(resA["advance_refunded"], usedA, usedB))
    check("After the A reversal balance = b0 - usedB (B still stands)",
          abs(db.get_advance_balance(customer) - (b0 - usedB)) < 0.001,
          "{} (should be {})".format(db.get_advance_balance(customer), b0 - usedB))

    resB = ops.cancel_document(docB, operator="ADMIN9", permissions=["admin"])
    check("Reversal of B refunded usedB", abs(resB["advance_refunded"] - usedB) < 0.001)
    check("After both reversals the balance is fully restored (b0)",
          abs(db.get_advance_balance(customer) - b0) < 0.001,
          "{} (should be {})".format(db.get_advance_balance(customer), b0))

    # Phantom: a cash sale WITHOUT an advance — cancelling it refunds 0 (not the other 'N' total)
    rC = ops.sell(customer_id=customer, invoice_date="2026-07-18", payment_method="cash",
                  lines=[{"code": k1, "supplier_code": f1, "price": 150, "qty": 1}],
                  operator="OWNER1", allow_below_min=True)
    resC = ops.cancel_document(rC["document_id"], operator="ADMIN9", permissions=["admin"])
    check("Reversal of a cash sale without an advance refunds 0", abs(resC["advance_refunded"]) < 0.001,
          "refunded={}".format(resC["advance_refunded"]))

    db.close()
    for ext in ("", "-wal", "-shm"):
        pth = TEST + ext
        if os.path.exists(pth):
            try: os.remove(pth)
            except Exception: pass

    print("\n=== RESULTS ===\n  PASSED: {}\n  FAILED: {}".format(OK, FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
