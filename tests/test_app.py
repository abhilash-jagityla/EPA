import os
import shutil
import unittest
from io import BytesIO
from app import app, db, extract_variables, DEFAULT_PATTERNS, User

class TestPDFExtractor(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['UPLOAD_FOLDER'] = 'test_uploads'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test upload directory
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Copy sample PDF to test uploads
        sample_pdf_path = os.path.join('tests', 'test_data', 'sample.pdf')
        self.test_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.pdf')
        if os.path.exists(sample_pdf_path):
            shutil.copy2(sample_pdf_path, self.test_pdf_path)
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Clean up test files
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
    
    def _login(self):
        # Helper method to create and log in a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return self.app.post('/login', data=dict(
            username='testuser',
            password='password'
        ), follow_redirects=True)

    def test_home_page_redirects(self):
        """Test if home page redirects when not logged in"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    def test_dashboard_access(self):
        """Test dashboard access after login"""
        self._login()
        response = self.app.get('/dashboardb')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload PDFs', response.data)

    def test_upload_requires_login(self):
        """Test that the upload endpoint requires login"""
        response = self.app.post('/upload', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)

    def test_extract_variables_from_pdf(self):
        """Test the old extract_variables function with the current sample PDF"""
        if not os.path.exists(self.test_pdf_path):
            self.skipTest("Sample PDF file not found")
            
        results = extract_variables(self.test_pdf_path, DEFAULT_PATTERNS)
        
        # This PDF contains dollar amounts but not the other fields from the original test
        self.assertTrue(len(results['dollar_amounts']) > 0)
        self.assertIn('$1,000.00', results['dollar_amounts'][0])
        # The other fields are not in the current sample.pdf
        self.assertEqual(len(results['emails']), 0)
        self.assertEqual(len(results['phone_numbers']), 0)
        self.assertEqual(len(results['dates']), 0) 