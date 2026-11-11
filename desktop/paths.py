import os
from pathlib import Path
from platformdirs import user_data_dir


def data_dir():
    path = Path(
        os.environ.get(
            "TYPEATLAS_DATA_DIR",
            user_data_dir(os.environ.get("PROJECT_NAME", "TypeAtlas"), appauthor=False),
        )
    )
    path.mkdir(parents=True, exist_ok=True)
    return path
