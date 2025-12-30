from flask import Flask, jsonify
from flask_cors import CORS

from .config import settings
from .routers import dhcp, arp, vlans, interfaces, shapers

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(dhcp.bp)
app.register_blueprint(arp.bp)
app.register_blueprint(vlans.bp)
app.register_blueprint(interfaces.bp)
app.register_blueprint(shapers.bp)


@app.route("/")
def root():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "OPNsense Monitor"})


@app.route("/config")
def get_config():
    """Get frontend config (refresh interval)."""
    return jsonify({"refresh_interval": settings.refresh_interval})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
