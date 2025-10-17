import importlib, cProfile, pstats, io, os

def run():
    app_mod = importlib.import_module("app")
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
