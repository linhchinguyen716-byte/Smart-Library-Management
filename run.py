from backend.app import app, init_db
import os

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5001, debug=os.environ.get("FLASK_DEBUG") == "1")
