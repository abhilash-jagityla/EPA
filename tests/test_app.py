import os
import shutil
import unittest
from io import BytesIO
from app import app, extract_variables, DEFAULT_PATTERNS

class TestPDFExtractor(unittest.TestCase):
    def setUp(self):
        # Enable test mode and disable login + CSRF during tests
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            LOGIN_DISABLED=True,
            UPLOAD_FOLDER='test_uploads'
        )
        self.app = app.test_client()

        # Create test upload directory
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Copy sample PDF to test uploads
        sample_pdf_path = os.path.join('tests', 'test_data', 'sample.pdf')
        self.test_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.pdf')
        if os.path.exists(sample_pdf_path):
            shutil.copy2(sample_pdf_path, self.test_pdf_path)

    def tearDown(self):
        # Clean up test files and directory
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])

    def test_home_page(self):
        """Test if home page loads correctly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Abhilash PDF Extractor', response.data)

    def test_upload_no_file(self):
        """Test upload endpoint without file"""
        response = self.app.post('/upload')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No file part', response.data)

    def test_upload_empty_file(self):
        """Test upload endpoint with empty file selection"""
        response = self.app.post('/upload', data={
            'file': (BytesIO(b''), '')
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No selected file', response.data)

    def test_upload_invalid_file_type(self):
        """Test upload endpoint with invalid file type"""
        response = self.app.post('/upload', data={
            'file': (BytesIO(b'test content'), 'test.txt')
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid file type', response.data)

    def test_extract_variables(self):
        """Test variable extraction function"""
        if not os.path.exists(self.test_pdf_path):
            self.skipTest("Sample PDF file not found")

        results = extract_variables(self.test_pdf_path, DEFAULT_PATTERNS)

        self.assertTrue(any('test@email.com' in email for email in results['emails']))
        self.assertTrue(any('123-456-7890' in phone for phone in results['phone_numbers']))
        self.assertTrue(any('$100.00' in amount for amount in results['dollar_amounts']))
        self.assertTrue(any('01/01/2023' in date for date in results['dates']))

    def test_patterns_endpoint(self):
        """Test patterns endpoint"""
        response = self.app.get('/patterns')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'emails', response.data)
        self.assertIn(b'phone_numbers', response.data)
        self.assertIn(b'dates', response.data)
        self.assertIn(b'dollar_amounts', response.data)

if __name__ == '__main__':
    unittest.m
