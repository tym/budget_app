from flask_migrate import Migrate
from models.models import db

migrate = Migrate()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
