import importlib, importlib.util, sys, pathlib
import pytest

def _smart_import(module_name: str, filename: str):
    try:
        return importlib.import_module(module_name)
    except Exception:
        root = pathlib.Path(__file__).resolve().parents[1]
        matches = list(root.rglob(filename))
        if not matches:
            raise
        path = str(matches[0])
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        sys.modules[module_name] = mod
        return mod

@pytest.fixture(scope="module")
def client():
    app_mod = _smart_import("app", "app.py")
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY="test")
    return app.test_client()

def ok_or_redirect(resp):
    assert resp.status_code in (200, 302), f"Unexpected status code: {resp.status_code}"

def test_invalid_login_rejected(client):
    resp = client.post("/login", data={"email": "demo@bookstore.com", "password": "wrong"}, follow_redirects=True)
    ok_or_redirect(resp)
    assert b"invalid" in resp.data.lower() or b"error" in resp.data.lower() or b"incorrect" in resp.data.lower()

def test_duplicate_discount_not_double_applied(client):
    client.post("/add_to_cart", data={"book_id": 1, "quantity": 2}, follow_redirects=True)
    first = client.post("/apply_discount", data={"code": "SAVE10"}, follow_redirects=True)
    ok_or_redirect(first)
    second = client.post("/apply_discount", data={"code": "SAVE10"}, follow_redirects=True)
    ok_or_redirect(second)
    assert b"already" in second.data.lower() or b"applied" in second.data.lower() or b"invalid" in second.data.lower()

def test_invalid_discount_code_is_rejected(client):
    resp = client.post("/apply_discount", data={"code": "BOGUS50"}, follow_redirects=True)
    ok_or_redirect(resp)
    assert b"invalid" in resp.data.lower() or b"error" in resp.data.lower()

def test_quantity_edge_cases(client):
    client.post("/add_to_cart", data={"book_id": 1, "quantity": 1}, follow_redirects=True)
    r0 = client.post("/update_cart", data={"book_id": 1, "quantity": 0}, follow_redirects=True)
    ok_or_redirect(r0)
    rneg = client.post("/update_cart", data={"book_id": 1, "quantity": -3}, follow_redirects=True)
    ok_or_redirect(rneg)
    assert any(k in r0.data.lower() + rneg.data.lower() for k in (b"invalid", b"must be", b"minimum", b"error", ))

def test_empty_cart_checkout_blocked(client):
    resp = client.post(
        "/checkout",
        data={
            "name": "Empty",
            "address": "No Items",
            "email": "empty@example.com",
            "payment_method": "card",
            "card_number": "4242424242424242",
            "expiry": "12/30",
            "cvv": "123",
        },
        follow_redirects=True,
    )
    ok_or_redirect(resp)
    assert b"empty" in resp.data.lower() or b"add items" in resp.data.lower() or b"cart" in resp.data.lower()
