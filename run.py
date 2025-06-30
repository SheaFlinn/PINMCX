from app import create_app, db
from flask_migrate import upgrade
from app.models import User, Market, Prediction

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Market': Market, 'Prediction': Prediction}

if __name__ == "__main__":
    app.run()
