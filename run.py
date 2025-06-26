import os
print("⚠️  Flask running from:", os.getcwd())

from app import create_app
from app.extensions import db
from app.models import User
from flask import send_from_directory

app = create_app()

@app.route('/debug-badge')
def debug_badge():
    return send_from_directory('static/badges', 'master_predictor.svg')

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
