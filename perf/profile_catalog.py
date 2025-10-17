import importlib, cProfile, pstats, io, os

def run():
    app_mod = importlib.import_module("app")
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, SECRET_KEY="ci")
    client = app.test_client()
    pr = cProfile.Profile()
    pr.enable()
    client.get("/")
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(30)
    os.makedirs("perf_artifacts", exist_ok=True)
    with open("perf_artifacts/catalog_profile.txt", "w") as f:
        f.write(s.getvalue())

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[profile_catalog] Skipped due to error: {e}")
