import importlib, cProfile, pstats, io, os, importlib.util, sys, pathlib

def _import_by_filename(module_name: str, filename: str):
    root = pathlib.Path(".").resolve()
    matches = list(root.rglob(filename))
    if not matches:
        raise ImportError(f"Cannot find {filename}")
    path = str(matches[0])
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules[module_name] = mod
    return mod

def _ensure_models_then_app():
    try:
        importlib.import_module("models")
    except Exception:
        _import_by_filename("models", "models.py")
    try:
        return importlib.import_module("app")
    except Exception:
        return _import_by_filename("app", "app.py")

def run():
    app_mod = _ensure_models_then_app()
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, SECRET_KEY="ci")
    client = app.test_client()
    client.post("/add_to_cart", data={"book_id": 1, "quantity": 3})
    client.post("/apply_discount", data={"code": "SAVE10"})
    pr = cProfile.Profile()
    pr.enable()
    client.post(
        "/checkout",
        data={
            "name": "CI",
            "address": "123 Test",
            "email": "ci@example.com",
            "payment_method": "card",
            "card_number": "4242424242424242",
            "expiry": "12/30",
            "cvv": "123",
        },
    )
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(30)
    os.makedirs("perf_artifacts", exist_ok=True)
    with open("perf_artifacts/checkout_profile.txt", "w") as f:
        f.write(s.getvalue())

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[profile_checkout] Skipped due to error: {e}")
