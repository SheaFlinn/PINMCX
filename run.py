import os
print("⚠️  Flask running from:", os.getcwd())

from app import create_app
from app.extensions import db
from app.models import User
from flask import send_from_directory, render_template

app = create_app()

@app.route('/debug-badge')
def debug_badge():
    return send_from_directory('static/badges', 'master_predictor.svg')

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 error: {str(e)}")
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}", exc_info=True)
    return render_template("500.html"), 500

if __name__ == '__main__':
    # Create admin user if it doesn't exist
    with app.app_context():
        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
    
    app.run(host='0.0.0.0', port=5001)
