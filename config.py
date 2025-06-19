import os
from datetime import timedelta

class Config:
    # General Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_TYPE = 'filesystem'
    
    # Security config
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Upload config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Azure AD SSO config (for future use)
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    AZURE_AUTHORITY = f'https://login.microsoftonline.com/{AZURE_TENANT_ID}'
    AZURE_SCOPE = ['User.Read']  # Add more scopes as needed 