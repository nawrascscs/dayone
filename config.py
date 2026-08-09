import os
from dotenv import load_dotenv

# Load local environment variables from .env and override any existing values.
load_dotenv(override=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-super-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:123456@localhost:5432/dayone'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
