import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///aquaguard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEVICE_API_TOKEN = os.getenv('DEVICE_API_TOKEN')
    SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME')
    SUPER_ADMIN_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')
    KIOSK_API_TOKEN = os.getenv('KIOSK_API_TOKEN')
    MOVING_AVERAGE_WINDOW = int(os.getenv('MOVING_AVERAGE_WINDOW', '5'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16384'))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError('SECRET_KEY must be set. Copy .env.example and generate a random value.')
        if os.getenv('VERCEL') and cls.SQLALCHEMY_DATABASE_URI.startswith('sqlite:'):
            raise RuntimeError('DATABASE_URL must use a persistent external database on Vercel; SQLite storage is ephemeral.')
