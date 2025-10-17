import importlib, importlib.util, sys, pathlib
from typing import Optional, Tuple, List

def _import_by_filename(module_name: str, filename: str):
    root = pathlib.Path(__file__).resolve().parents[1]
    matches = list(root.rglob(filename))
    if not matches:
        raise ImportError(f"Cannot find {filename} from {root}")
    path = str(matches[0])
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules[module_name] = mod
    return mod

def _smart_import(module_name: str, filename: str):
    try:
        return importlib.import_module(module_name)
    except Exception:
        return _import_by_filename(module_name, filename)

def _ensure_models_then_app():
    try:
        importlib.import_module("models")
    except Exception:
        _import_by_filename("models", "models.py")
    try:
        return importlib.import_module("app")
    except Exception:
        return _import_by_filename("app", "app.py")

def _post_first(client, path_candidates: List[str], data) -> Tuple[Optional[object], Optional[str]]:
    for p in path_candidates:
        resp = client.post(p, data=data, follow_redirects=True)
        if resp.status_code in (200, 302):
            return resp, p
        if resp.status_code not in (404, 405):
            return resp, p
    return None, None

def _get_first(client, path_candidates: List[str]) -> Tuple[Optional[object], Optional[str]]:
    for p in path_candidates:
        resp = client.get(p, follow_redirects=True)
        if resp.status_code in (200, 302):
            return resp, p
        if resp.status_code not in (404, 405):
            return resp, p
    return None, None

def ok_or_redirect(resp):
    assert resp is not None, "No response received"
    assert resp.status_code in (200, 302), f"Unexpected status code: {resp.status_code}"

import pytest

ADD_TO_CART = ["/add_to_cart", "/cart/add", "/api/cart/add"]
VIEW_CART   = ["/cart", "/view_cart"]
UPDATE_CART = ["/update_cart", "/cart/update", "/api/cart/update"]
REMOVE_CART = ["/remove_from_cart", "/cart/remove", "/api/cart/remove"]
DISCOUNTS   = ["/apply_discount", "/discount/apply", "/coupon/apply"]

@pytest.fixture(scope="module")
def client():
    app_mod = _ensure_models_then_app()
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY="test")
    return app.test_client()

def test_homepage_lists_books(client):
    resp, _ = _get_first(client, ["/", "/home", "/index"])
    ok_or_redirect(resp)
    assert any(k in resp.data for k in (b"Book", b"Featured", b"Catalog", b"Home"))

def test_login_logout_cycle(client):
    resp, _ = _get_first(client, ["/login", "/auth/login"])
    ok_or_redirect(resp)
    resp, _ = _post_first(client, ["/login", "/auth/login"], {"email": "demo@bookstore.com", "password": "demo123"})
    ok_or_redirect(resp)
    resp, _ = _get_first(client, ["/logout", "/auth/logout"])
    ok_or_redirect(resp)

def test_register_then_login(client):
    resp, _ = _get_first(client, ["/register", "/auth/register"])
    ok_or_redirect(resp)
    email = "testuser+ci@example.com"
    resp, _ = _post_first(client, ["/register", "/auth/register"], {"email": email, "password": "pw12345"})
    ok_or_redirect(resp)
    resp, _ = _post_first(client, ["/login", "/auth/login"], {"email": email, "password": "pw12345"})
    ok_or_redirect(resp)

def test_cart_add_update_remove_flow(client):
    resp, used_add = _post_first(client, ADD_TO_CART, {"book_id": 1, "quantity": 2})
    ok_or_redirect(resp)
    resp, _ = _get_first(client, VIEW_CART)
    ok_or_redirect(resp)
    resp, used_update = _post_first(client, [used_add.replace("add", "update")] + UPDATE_CART if used_add else UPDATE_CART, {"book_id": 1, "quantity": 3})
    ok_or_redirect(resp)
    resp, _ = _post_first(client, [used_add.replace("add", "remove")] + REMOVE_CART if used_add else REMOVE_CART, {"book_id": 1})
    ok_or_redirect(resp)

def test_discount_codes_and_checkout(client):
    _post_first(client, ADD_TO_CART, {"book_id": 1, "quantity": 1})
    resp, used_disc = _post_first(client, DISCOUNTS, {"code": "SAVE10"})
    # allow skip if app has no discount endpoints
    if not resp:
        pytest.skip("No working discount endpoint found in app; skipping test.")
    resp, _ = _get_first(client, ["/checkout", "/order/checkout"])
    ok_or_redirect(resp)
    resp, _ = _post_first(client, ["/checkout", "/order/checkout"], {
        "name": "Alice",
        "address": "1 Test St",
        "email": "alice@example.com",
        "payment_method": "card",
        "card_number": "4242424242424242",
        "expiry": "12/30",
        "cvv": "123",
    })
    ok_or_redirect(resp)
    resp, _ = _post_first(client, ["/checkout", "/order/checkout"], {
        "name": "Bob",
        "address": "2 Test St",
        "email": "bob@example.com",
        "payment_method": "card",
        "card_number": "4111111111111111",
        "expiry": "12/30",
        "cvv": "111",
    })
    ok_or_redirect(resp)
    assert (b"failed" in resp.data.lower() or b"error" in resp.data.lower() or b"declined" in resp.data.lower()),         "Expected a payment failure message when card ends with 1111"
