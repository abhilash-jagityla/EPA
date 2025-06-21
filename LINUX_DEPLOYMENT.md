# Linux Deployment Guide

This guide provides step-by-step instructions for deploying the Abhilash PDF Extractor on a Linux VM in production.

## System Requirements

- Ubuntu 20.04 LTS or newer (these instructions are Ubuntu-specific)
- 2GB RAM minimum (4GB recommended)
- 20GB storage
- Python 3.9 or newer

## Initial Server Setup

1. Update the system:
```bash
sudo apt update
sudo apt upgrade -y
```

2. Install required system packages:
```bash
sudo apt install -y python3-pip python3-venv nginx supervisor git
```

3. Create a dedicated user for the application:
```bash
sudo useradd -m -s /bin/bash webapps
sudo usermod -aG sudo webapps
```

## Application Deployment

1. Switch to the webapps user and clone the repository:
```bash
sudo su - webapps
git clone <repository-url> /home/webapps/EPA
cd /home/webapps/EPA
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install production dependencies:
```bash
pip install -r requirements.txt
pip install gunicorn  # Production web server
```

4. Create production configuration:
```bash
sudo mkdir -p /etc/EPA
sudo nano /etc/EPA/config.py
```

Add the following content (replace with your values):
```python
import os
from datetime import timedelta

class Config:
    # Production settings
    SECRET_KEY = 'your-very-secure-secret-key'  # Change this!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # Use PostgreSQL for production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Enable if using HTTPS
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = '/home/webapps/EPA/uploads'
```

5. Create required directories:
```bash
mkdir -p /home/webapps/EPA/uploads
mkdir -p /home/webapps/EPA/logs
```

## Gunicorn Setup

1. Create Gunicorn configuration:
```bash
sudo nano /etc/EPA/gunicorn.conf.py
```

Add the following content:
```python
import multiprocessing

bind = "unix:/home/webapps/EPA/EPA.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
errorlog = "/home/webapps/EPA/logs/gunicorn-error.log"
accesslog = "/home/webapps/EPA/logs/gunicorn-access.log"
loglevel = "info"
```

## Supervisor Configuration

1. Create supervisor configuration:
```bash
sudo vi /etc/supervisor/conf.d/EPA.conf
```

Add the following content:
```ini
[program:EPA]
directory=/home/webapps/EPA
command=/home/webapps/EPA/venv/bin/gunicorn -c /etc/EPA/gunicorn.conf.py app:app
user=webapps
autostart=true
autorestart=true
stderr_logfile=/home/webapps/EPA/logs/supervisor-err.log
stdout_logfile=/home/webapps/EPA/logs/supervisor-out.log
environment=PATH="/home/webapps/EPA/venv/bin"
```

2. Update supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl updated
```

## Nginx Configuration

1. Create Nginx configuration:
```bash
sudo vi /etc/nginx/sites-available/EPA
```

Add the following content:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    access_log /home/webapps/EPA/logs/nginx-access.log;
    error_log /home/webapps/EPA/logs/nginx-error.log;

    location / {
        proxy_pass http://unix:/home/webapps/EPA/EPA.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        
        # Upload size
        client_max_body_size 16M;
    }

    location /static {
        alias /home/webapps/EPA/static;
        expires 30d;
    }
}
```

2. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/EPA /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## SSL/HTTPS Setup (Recommended)

1. Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

2. Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com
```

## Final Steps

1. Set proper permissions:
```bash
sudo chown -R webapps:webapps /home/webapps/EPA
sudo chmod -R 755 /home/webapps/EPA
```

2. Start the application:
```bash
sudo supervisorctl start EPA
```

## Monitoring and Maintenance

### Check Application Status
```bash
sudo supervisorctl status EPA
```

### View Logs
```bash
# Application logs
tail -f /home/webapps/EPA/logs/supervisor-out.log
tail -f /home/webapps/EPA/logs/supervisor-err.log

# Nginx logs
tail -f /home/webapps/EPA/logs/nginx-access.log
tail -f /home/webapps/EPA/logs/nginx-error.log
```

### Restart Application
```bash
sudo supervisorctl restart EPA
```

### Update Application
```bash
cd /home/webapps/EPA
source venv/bin/activate
git pull
pip install -r requirements.txt
sudo supervisorctl restart EPA
```

## Backup

1. Database backup (if using SQLite):
```bash
cp /home/webapps/EPA/app.db /home/webapps/backups/app.db.$(date +%Y%m%d)
```

2. Configuration backup:
```bash
sudo cp -r /etc/EPA /home/webapps/backups/config.$(date +%Y%m%d)
```

## Security Recommendations

1. Configure UFW firewall:
```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

2. Set up automatic security updates:
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

3. Regularly update system packages:
```bash
sudo apt update
sudo apt upgrade
```

## Troubleshooting

1. If the application fails to start:
```bash
sudo supervisorctl status EPA
tail -f /home/webapps/EPA/logs/supervisor-err.log
```

2. If Nginx returns 502 Bad Gateway:
```bash
tail -f /home/webapps/EPA/logs/gunicorn-error.log
sudo nginx -t
```

3. Check permissions:
```bash
ls -la /home/webapps/EPA
ls -la /home/webapps/EPA/EPA.sock
```

4. Restart all services:
```bash
sudo supervisorctl restart EPA
sudo systemctl restart nginx
``` 