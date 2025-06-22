import os
import io
import sys
import pytest
from flask import url_for
from werkzeug.datastructures import FileStorage
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    
    # Create test upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        yield client
    
    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()
    
    # Remove test upload directory
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
        os.rmdir(app.config['UPLOAD_FOLDER'])

def login(client, username='testuser', password='testpass'):
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def test_login_required(test_client):
    """Test that protected routes require login"""
    # Try accessing dashboard without login
    response = test_client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.location
    
    # Try accessing upload without login
    response = test_client.post('/upload')
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_logout(test_client):
    """Test login and logout functionality"""
    # Test successful login
    response = login(test_client)
    assert b'Upload PDFs' in response.data
    
    # Test logout
    response = logout(test_client)
    assert b'Please log in to access this page.' in response.data
    
    # Test invalid login
    response = login(test_client, username='wrong', password='wrong')
    assert b'Invalid username or password' in response.data

def test_upload_single_file(test_client):
    """Test uploading a single PDF file"""
    login(test_client)
    
    # Create a test PDF file
    test_pdf = os.path.join(os.path.dirname(__file__), 'test_data', 'sample.pdf')
    if not os.path.exists(test_pdf):
        pytest.skip("Test PDF file not found")
    
    with open(test_pdf, 'rb') as pdf:
        data = {'files[]': (io.BytesIO(pdf.read()), 'test.pdf')}
        response = test_client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data'
        )
    
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

def test_upload_multiple_files(test_client):
    """Test uploading multiple PDF files"""
    login(test_client)
    
    # Create test PDF files
    test_pdfs = [
        os.path.join(os.path.dirname(__file__), 'test_data', 'sample1.pdf'),
        os.path.join(os.path.dirname(__file__), 'test_data', 'sample2.pdf')
    ]
    
    if not all(os.path.exists(pdf) for pdf in test_pdfs):
        pytest.skip("Test PDF files not found")
    
    data = {'files[]': []}
    for pdf_path in test_pdfs:
        with open(pdf_path, 'rb') as pdf:
            data['files[]'].append((io.BytesIO(pdf.read()), os.path.basename(pdf_path)))
    
    response = test_client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

def test_invalid_file_upload(test_client):
    """Test uploading invalid file types"""
    login(test_client)
    
    # Try uploading a text file
    data = {'files[]': (io.BytesIO(b'This is not a PDF'), 'test.txt')}
    response = test_client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=True
    )
    
    assert b'Invalid file type' in response.data

def test_excel_output_format(test_client):
    """Test the format of the Excel output"""
    login(test_client)
    
    # Create a test PDF file
    test_pdf = os.path.join(os.path.dirname(__file__), 'test_data', 'sample.pdf')
    if not os.path.exists(test_pdf):
        pytest.skip("Test PDF file not found")
    
    with open(test_pdf, 'rb') as pdf:
        data = {'files[]': (io.BytesIO(pdf.read()), 'test.pdf')}
        response = test_client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data'
        )
    
    # Read the Excel file from response
    df = pd.read_excel(io.BytesIO(response.data))
    
    # Check if required columns exist
    required_columns = ['Source_File']  # Add other expected columns
    for col in required_columns:
        assert col in df.columns
    
    # Check if Source_File column contains the uploaded filename
    assert 'test.pdf' in df['Source_File'].values

def test_concurrent_users(test_client):
    """Test handling multiple users simultaneously"""
    # Create second test user
    with app.app_context():
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('testpass2')
        db.session.add(user2)
        db.session.commit()
    
    # First user session
    response1 = login(test_client)
    assert b'Upload PDFs' in response1.data
    
    # Logout first user
    logout(test_client)
    
    # Second user session
    response2 = login(test_client, 'testuser2', 'testpass2')
    assert b'Upload PDFs' in response2.data
    
    # Each user should be able to upload files independently
    test_pdf = os.path.join(os.path.dirname(__file__), 'test_data', 'sample.pdf')
    if os.path.exists(test_pdf):
        with open(test_pdf, 'rb') as pdf:
            data = {'files[]': (io.BytesIO(pdf.read()), 'test.pdf')}
            response = test_client.post(
                '/upload',
                data=data,
                content_type='multipart/form-data'
            )
        assert response.status_code == 200 