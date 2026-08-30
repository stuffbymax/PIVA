"""
Entrypoint for running the Flask dev server directly on the host
(no Docker). Run from inside backend/:

    python run.py
"""

import os

from dotenv import find_dotenv, load_dotenv

# Searches this directory and parent directories for a .env file, so
# a single .env at the project root (next to schema.sql / ini.py) is
# picked up automatically even though this script lives in backend/.
load_dotenv(find_dotenv(usecwd=True))

from app import create_app  # noqa: E402  (import after dotenv load on purpose)

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = app.config["DEBUG"]
    app.run(host=host, port=port, debug=debug)
