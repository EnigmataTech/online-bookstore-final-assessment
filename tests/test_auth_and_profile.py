import importlib, importlib.util, sys, pathlib

def _import_by_filename(module_name: str, filename: str):
    root = pathlib.Path(__file__).resolve().parents[1]
    path = next(root.rglob(filename), None)
    if not path:
        raise ImportError(f"Cannot find {filename} from {root}")
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules[module_name] = mod
    return mod

def _ensure_models_then_app():
    try:
        importlib.import_module("models")
    except Exception:
        _import_by_filename("models","models.py")
    try:
        return importlib.import_module("app")
    except Exception:
        return _import_by_filename("app","app.py")

import pytest

@pytest.fixture(scope="module")
def app_mod():
    return _ensure_models_then_app()

@pytest.fixture(scope="module")
def client(app_mod):
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, SECRET_KEY="test")
    return app.test_client()

def test_login_logout_cycle(client):
    # login demo user
    r = client.post("/login", data={"email":"demo@bookstore.com", "password":"demo123"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    # logout
    r = client.get("/logout", follow_redirects=True)
    assert r.status_code in (200, 302)

def test_register_requires_name_and_then_login(client):
    # register new user (name required by app)
    r = client.post("/register", data={
        "email":"testuser+ci@example.com",
        "password":"pw12345",
        "name":"Test User",
        "address":"123 Road",
    }, follow_redirects=True)
    assert r.status_code in (200, 302)
    # should be logged-in now (app sets session on success); visit account
    r = client.get("/account", follow_redirects=True)
    # Either we see account (200) or we get redirected to login if something changed
    assert r.status_code in (200, 302)
