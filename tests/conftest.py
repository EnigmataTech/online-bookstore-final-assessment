import importlib, importlib.util, sys, pathlib, pytest

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

@pytest.fixture(scope="session")
def app_mod():
    return _ensure_models_then_app()

@pytest.fixture(scope="function")
def client(app_mod):
    app = getattr(app_mod, "app")
    app.config.update(TESTING=True, SECRET_KEY="test")
    with app.test_client() as c:
        yield c
