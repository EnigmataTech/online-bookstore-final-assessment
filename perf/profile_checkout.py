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
    """
    Profile checkout process with correct endpoints.
    Fixed: Updated endpoints to match current app routes.
    """
    app_mod = _ensure_models_then_app()
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, SECRET_KEY="ci")
    client = app.test_client()

    # Add item to cart using correct endpoint
    client.post("/add-to-cart", data={"title": "1984", "quantity": 3})

    pr = cProfile.Profile()
    pr.enable()

    # Profile the checkout process
    client.post(
        "/process-checkout",  # Correct endpoint
        data={
            "name": "CI User",
            "address": "123 Test St",
            "city": "TestCity",
            "zip_code": "12345",
            "email": "ci@example.com",
            "payment_method": "credit_card",
            "card_number": "4242424242424242",
            "expiry_date": "12/30",
            "cvv": "123",
            "discount_code": "SAVE10",
        },
    )

    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(30)
    os.makedirs("perf_artifacts", exist_ok=True)
    with open("perf_artifacts/checkout_profile.txt", "w") as f:
        f.write(s.getvalue())
    print("[profile_checkout] Profile saved to perf_artifacts/checkout_profile.txt")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[profile_checkout] Skipped due to error: {e}")
