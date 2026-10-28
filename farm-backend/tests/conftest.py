import sys
from pathlib import Path

# make "import app...." work when running `pytest` from farm_backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
