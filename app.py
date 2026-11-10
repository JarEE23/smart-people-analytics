import os
from flask import Flask, render_template
from config import Config
from models import init_db
from services.analytics_service import AnalyticsService
from services.simulator import generate_simulated_dataset

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database
    with app.app_context():
        init_db()
        # Seed simulated dataset if database is empty
        range_info = AnalyticsService.get_available_date_range()
        if range_info.get("total_records", 0) == 0:
            print("[INFO] Database kosong terdeteksi. Melakukan seeding data simulasi 14 hari...")
            generate_simulated_dataset(days=14)
            print("[INFO] Seeding data simulasi selesai.")

    # Register Blueprints
    from routes.dashboard import dashboard_bp
    from routes.events import events_bp
    from routes.chat import chat_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)

    @app.context_processor
    def inject_global_vars():
        return {
            "app_name": "Smart People Analytics",
            "app_subtitle": "AI Chat Analyst & Computer Vision Monitor",
            "student_name": "Fajar",
            "project_type": "Kapita Selekta / TA"
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_message="Halaman tidak ditemukan (404)"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_message="Terjadi kesalahan pada server (500)"), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f" Smart People Analytics — AI Chat Analyst Running")
    print(f" URL: http://127.0.0.1:{port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
