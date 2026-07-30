from pathlib import Path

from flask import Flask, send_from_directory

PUBLIC = Path(__file__).with_name("public")
app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    return send_from_directory(PUBLIC, path if (PUBLIC / path).is_file() else "index.html")


if __name__ == "__main__":
    app.run()
