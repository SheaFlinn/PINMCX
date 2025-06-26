from app import create_app
from app.extensions import db
from flask_migrate import upgrade

app = create_app()

@app.before_first_request
def initialize_database():
    """Apply migrations on first request (for dev/demo purposes)."""
    with app.app_context():
        upgrade()

if __name__ == '__main__':
    app.run(debug=True)
