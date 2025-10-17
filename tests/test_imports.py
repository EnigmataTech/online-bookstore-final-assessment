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
    # Ensure models is available before importing app (app may import models)
    try:
        importlib.import_module("models")
    except Exception:
        _import_by_filename("models", "models.py")
    try:
        return importlib.import_module("app")
    except Exception:
        return _import_by_filename("app", "app.py")

def test_app_imports():
    mod = _ensure_models_then_app()
    app_obj = getattr(mod, "app", None)
    assert app_obj is not None, "Expected Flask app instance named 'app' in app.py"

def test_models_imports():
    mod = _smart_import("models", "models.py")
    assert hasattr(mod, "Book"), "models.Book missing"
    assert hasattr(mod, "Cart"), "models.Cart missing"
