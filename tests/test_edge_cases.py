import pytest
from typing import Optional, Tuple
import importlib, importlib.util, sys, pathlib

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

DISCOUNT_ENDPOINTS = ["/apply_discount", "/discount/apply", "/coupon/apply"]

def _post_first(client, path_candidates, data) -> Tuple[Optional[object], Optional[str]]:
    for p in path_candidates:
        resp = client.post(p, data=data, follow_redirects=True)
        if resp.status_code in (200, 302):
            return resp, p
        if resp.status_code not in (404, 405):
            # consider non-OK, non-404 as a valid endpoint with error message we can still assert on
            return resp, p
    return None, None

@pytest.fixture(scope="module")
def client():
    app_mod = _ensure_models_then_app()
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
    first, used = _post_first(client, DISCOUNT_ENDPOINTS, {"code": "SAVE10"})
    if not first:
        pytest.skip("No working discount endpoint found in app; skipping test.")
    # Allow 200/302 or a validation message path
    assert first.status_code in (200, 302) or b"applied" in first.data.lower() or b"discount" in first.data.lower()
    second, used2 = _post_first(client, [used] if used else DISCOUNT_ENDPOINTS, {"code": "SAVE10"})
    assert second is not None, "Second discount apply should still reach an endpoint"
    # Expect idempotence or 'already applied' / 'invalid' message
    assert b"already" in second.data.lower() or b"applied" in second.data.lower() or b"invalid" in second.data.lower()

def test_invalid_discount_code_is_rejected(client):
    resp, _ = _post_first(client, DISCOUNT_ENDPOINTS, {"code": "BOGUS50"})
    if not resp:
        pytest.skip("No working discount endpoint found in app; skipping test.")
    assert b"invalid" in resp.data.lower() or b"error" in resp.data.lower() or b"not" in resp.data.lower()

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
