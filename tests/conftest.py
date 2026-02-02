from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if "fastembed" not in sys.modules:
    fastembed_stub = types.ModuleType("fastembed")

    class _StubTextEmbedding:
        def __init__(self, *args, **kwargs):
            pass

        def embed(self, texts):
            for _ in texts:
                yield [0.0, 0.0, 0.0]

    fastembed_stub.TextEmbedding = _StubTextEmbedding
    sys.modules["fastembed"] = fastembed_stub
