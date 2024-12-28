class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://tyborg:546f7b5b4e2e1b90e91081b3c51cd5e8c5084ab1149885dd32f8740bef4c19bd@localhost:5432/budget'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable Debugging
    FLASK_ENV = 'development'  # This enables development environment
    DEBUG = True  # This enables Flask's debug mode