from pathlib import Path
import sys
from flask import Flask, render_template

# Load .env if present (project root)
try:  # lightweight optional
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env', override=False)
except Exception:
    pass

# Ensure we can import dashboard.* when running as `python dashboard/app.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.services.stats_service import get_statistics  # noqa: E402
from dashboard.routes.stats import stats_bp  # noqa: E402

app = Flask(__name__)
app.register_blueprint(stats_bp)

@app.route('/')
def index():
    stats = get_statistics()
    return render_template('index.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True)