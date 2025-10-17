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

def test_homepage_lists_books(client):
    resp = client.get("/")
    ok_or_redirect(resp)
    assert any(k in resp.data for k in (b"Book", b"Featured", b"Catalog"))

def test_login_logout_cycle(client):
    resp = client.get("/login")
    ok_or_redirect(resp)
    resp = client.post("/login", data={"email": "demo@bookstore.com", "password": "demo123"}, follow_redirects=True)
    ok_or_redirect(resp)
    resp = client.get("/logout", follow_redirects=True)
    ok_or_redirect(resp)

def test_register_then_login(client):
    resp = client.get("/register")
    ok_or_redirect(resp)
    email = "testuser+ci@example.com"
    resp = client.post("/register", data={"email": email, "password": "pw12345"}, follow_redirects=True)
    ok_or_redirect(resp)
    resp = client.post("/login", data={"email": email, "password": "pw12345"}, follow_redirects=True)
    ok_or_redirect(resp)

def test_cart_add_update_remove_flow(client):
    tried = False
    for path in ["/add_to_cart", "/cart/add"]:
        resp = client.post(path, data={"book_id": 1, "quantity": 2}, follow_redirects=True)
        if resp.status_code in (200, 302):
            tried = True
            break
    assert tried, "Could not find a working add_to_cart endpoint"
    for path in ["/cart", "/view_cart"]:
        resp = client.get(path)
        if resp.status_code in (200, 302):
            break
    ok_or_redirect(resp)
    for path in ["/update_cart", "/cart/update"]:
        resp = client.post(path, data={"book_id": 1, "quantity": 3}, follow_redirects=True)
        if resp.status_code in (200, 302):
            break
    ok_or_redirect(resp)
    for path in ["/remove_from_cart", "/cart/remove"]:
        resp = client.post(path, data={"book_id": 1}, follow_redirects=True)
        if resp.status_code in (200, 302):
            break
    ok_or_redirect(resp)

def test_discount_codes_and_checkout(client):
    client.post("/add_to_cart", data={"book_id": 1, "quantity": 1}, follow_redirects=True)
    applied = False
    for code in ("SAVE10", "WELCOME20"):
        for path in ["/apply_discount", "/discount/apply"]:
            resp = client.post(path, data={"code": code}, follow_redirects=True)
            if resp.status_code in (200, 302):
                applied = True
                break
        if applied:
            break
    resp = client.get("/checkout")
    ok_or_redirect(resp)
    resp = client.post(
        "/checkout",
        data={
            "name": "Alice",
            "address": "1 Test St",
            "email": "alice@example.com",
            "payment_method": "card",
            "card_number": "4242424242424242",
            "expiry": "12/30",
            "cvv": "123",
        },
        follow_redirects=True,
    )
    ok_or_redirect(resp)
    resp = client.post(
        "/checkout",
        data={
            "name": "Bob",
            "address": "2 Test St",
            "email": "bob@example.com",
            "payment_method": "card",
            "card_number": "4111111111111111",
            "expiry": "12/30",
            "cvv": "111",
        },
        follow_redirects=True,
    )
    ok_or_redirect(resp)
    assert (b"failed" in resp.data.lower() or b"error" in resp.data.lower() or b"declined" in resp.data.lower()),         "Expected a payment failure message when card ends with 1111"
