import importlib, importlib.util, sys, pathlib

def _smart_import(module_name: str, filename: str):
    try:
        return importlib.import_module(module_name)
    except Exception:
        # Fallback: locate file anywhere in repo
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

def test_app_imports():
    mod = _smart_import("app", "app.py")
    app_obj = getattr(mod, "app", None)
    assert app_obj is not None, "Expected Flask app instance named 'app' in app.py"

def test_models_imports():
    mod = _smart_import("models", "models.py")
    assert hasattr(mod, "Book"), "models.Book missing"
    assert hasattr(mod, "Cart"), "models.Cart missing"
