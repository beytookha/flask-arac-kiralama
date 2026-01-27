import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    """Temel konfigürasyon ayarları."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'varsayilan-guvensiz-anahtar'
    
    # DB Ayarları
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME')
    
    # E-posta Ayarları
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Rent-A-Car Kurumsal', MAIL_USERNAME)

    # Dosya Yükleme
    UPLOAD_FOLDER = os.path.join('static', 'img')
    PROFILE_UPLOAD_FOLDER = os.path.join('static', 'img', 'profiles')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
