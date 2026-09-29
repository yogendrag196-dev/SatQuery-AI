"""
app.py
Main entrypoint for the SatQuery AI Backend REST Server
Supports both /api/* and top-level /vlm/* routes.
"""

from flask import Flask
from flask_cors import CORS
from config import Config
from routes.api import api_bp

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_bp, url_prefix='', name='top_level_api')

    return app

if __name__ == '__main__':
    app = create_app()
    print(f"[SATQUERY-AI] Mission Control Server starting on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, threaded=True)
