# Windows Deployment Guide (Development/Testing)

This guide provides instructions for deploying the Abhilash PDF Extractor on a Windows desktop for testing purposes.

## System Requirements

- Windows 10 or Windows 11
- Python 3.9 or newer
- Git for Windows
- 2GB RAM minimum
- 10GB free disk space

## Installation Steps

1. Install Required Software:
   - Download and install [Python](https://www.python.org/downloads/) (Check "Add Python to PATH" during installation)
   - Download and install [Git for Windows](https://gitforwindows.org/)

2. Clone the Repository:
```powershell
# Open PowerShell as Administrator
cd C:\Projects  # Or your preferred directory
git clone <repository-url> pdf-extractor
cd pdf-extractor
```

3. Create and Activate Virtual Environment:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

4. Install Dependencies:
```powershell
pip install -r requirements.txt
pip install waitress  # Windows production server
```

5. Create Configuration:
```powershell
mkdir config
```

Create a new file `config\production.py` with the following content:
```python
import os
from datetime import timedelta

class Config:
    # Production settings
    SECRET_KEY = 'your-secure-key-here'  # Change this!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
```

6. Create Required Directories:
```powershell
mkdir uploads
mkdir logs
```

## Create Startup Scripts

1. Create a file named `start_server.ps1`:
```powershell
# Create start_server.ps1 with the following content:
$env:FLASK_ENV = "production"
$env:FLASK_APP = "app.py"

# Activate virtual environment
.\venv\Scripts\activate

# Start Waitress server
python -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=8000, url_scheme='http')"
```

2. Create a file named `start_server.bat`:
```batch
@echo off
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {.\start_server.ps1}"
pause
```

## Running the Application

### Method 1: Using PowerShell (Recommended)
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope Process
.\start_server.ps1
```

### Method 2: Using Batch File
Simply double-click `start_server.bat`

The application will be available at `http://localhost:8000`

## Windows Firewall Configuration

1. Allow HTTP Traffic:
```powershell
# Open PowerShell as Administrator
New-NetFirewallRule -DisplayName "PDF Extractor App" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

## Accessing the Application

- Local access: `http://localhost:8000`
- Network access: `http://<your-ip-address>:8000`

To find your IP address:
```powershell
ipconfig
```

Look for the IPv4 Address under your active network adapter.

## Monitoring and Logs

1. View Application Logs:
```powershell
Get-Content -Path ".\logs\app.log" -Wait
```

2. Check Process Status:
```powershell
Get-Process -Name python
```

## Stopping the Server

1. Find the process:
```powershell
Get-Process -Name python | Where-Object {$_.MainWindowTitle -eq ""}
```

2. Stop the process:
```powershell
Stop-Process -Name python
```

## Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace XXXX with PID)
taskkill /PID XXXX /F
```

### Permission Issues
1. Run PowerShell as Administrator
2. Check folder permissions:
```powershell
icacls C:\Projects\pdf-extractor
```

3. Grant full permissions if needed:
```powershell
icacls C:\Projects\pdf-extractor /grant "Users:(OI)(CI)F"
```

### Database Issues
1. Delete the existing database:
```powershell
Remove-Item "app.db"
```

2. Restart the application to create a new database.

## Updating the Application

1. Stop the current server
2. Pull latest changes:
```powershell
git pull
```

3. Update dependencies:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

4. Restart the server using the startup script

## Security Notes

1. This setup is intended for testing/development purposes only
2. For proper production deployment on Windows, consider using:
   - IIS with FastCGI
   - Windows Server
   - Proper SSL/TLS certificates
   - Windows authentication integration

## Backup

1. Database backup:
```powershell
$date = Get-Date -Format "yyyyMMdd"
Copy-Item "app.db" -Destination "app.db.$date.backup"
```

2. Configuration backup:
```powershell
$date = Get-Date -Format "yyyyMMdd"
Copy-Item "config" -Destination "config.$date.backup" -Recurse
``` 