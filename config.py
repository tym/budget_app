class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://tymul:SCRAM-SHA-256$4096:0pJzYJVo7trG4iZrRcLzsg==$rMV57XTToYKNgDclqFCMK5/kIC/PJGrgUX2OqwFdkns=:PFRdGK3dafC8ZBhZ3K6u2+7c/vv3No+UsMmW8ZaD60c=@localhost:5432/budget'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable Debugging
    FLASK_ENV = 'development'  # This enables development environment
    DEBUG = True  # This enables Flask's debug mode