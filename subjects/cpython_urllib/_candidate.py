from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType


def load_candidate() -> ModuleType:
    repository = Path.cwd().resolve()
    candidate_lib = repository / "Lib"
    if not (candidate_lib / "urllib" / "parse.py").is_file():
        raise FileNotFoundError(f"Missing candidate urllib source under {candidate_lib}")
    for name in ("urllib.parse", "urllib"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(candidate_lib))
    module = importlib.import_module("urllib.parse")
    source = Path(inspect.getsourcefile(module.unquote_to_bytes) or "").resolve()
    if not source.is_relative_to(repository):
        raise RuntimeError(f"Imported {source}, not candidate source under {repository}")
    return module
