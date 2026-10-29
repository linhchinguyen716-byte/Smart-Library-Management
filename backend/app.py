"""Điểm tập hợp các route. Giữ tương thích `from backend.app import app, init_db`."""
from .core import app, init_db, db
from .routes import auth, dashboard, catalog, people, loans, reservations, reports, alerts, api

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5001, debug=False)
