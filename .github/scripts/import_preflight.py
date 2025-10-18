import importlib, importlib.util, sys, pathlib

def import_by_filename(modname, filename):
    root = pathlib.Path(".").resolve()
    path = next(root.rglob(filename), None)
    if path is None:
        raise SystemExit(f"Cannot find {filename}")
    spec = importlib.util.spec_from_file_location(modname, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules[modname] = mod
    return mod

def main():
    try:
        importlib.import_module("models")
    except Exception:
        import_by_filename("models", "models.py")

    try:
        app_mod = importlib.import_module("app")
    except Exception:
        app_mod = import_by_filename("app", "app.py")

    print("[OK] models:", sys.modules["models"].__file__)
    print("[OK] app:", app_mod.__file__)

if __name__ == "__main__":
    main()
