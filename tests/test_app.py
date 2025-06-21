import os
import shutil
import unittest
from io import BytesIO
from app import app, extract_variables, DEFAULT_PATTERNS


class TestPDFExtractor(unittest.TestCase):
    def setUp(self):
        # ── Test-only settings ────────────────────────────────────────────
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,   # disable CSRF for test posts
            LOGIN_DISABLED=True,      # bypass @login_required
            UPLOAD_FOLDER="test_uploads",
        )
        self.app = app.test_client()

        # prepare temp upload folder
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        sample_src = os.path.join("tests", "test_data", "sample.pdf")
        self.test_pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], "test.pdf")
        if os.path.exists(sample_src):
            shutil.copy2(sample_src, self.test_pdf_path)

    def tearDown(self):
        if os.path.exists(app.config["UPLOAD_FOLDER"]):
            shutil.rmtree(app.config["UPLOAD_FOLDER"])

    # ──────────────────────────────────────────────────────────────────────
    def test_home_page(self):
        resp = self.app.get("/", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Abhilash PDF Extractor", resp.data)

    def test_upload_no_file(self):
        resp = self.app.post("/upload", follow_redirects=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"No file part", resp.data)

    def test_upload_empty_file(self):
        resp = self.app.post(
            "/upload",
            data={"file": (BytesIO(b""), "")},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"No selected file", resp.data)

    def test_upload_invalid_file_type(self):
        resp = self.app.post(
            "/upload",
            data={"file": (BytesIO(b"dummy"), "test.txt")},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Invalid file type", resp.data)

    def test_extract_variables(self):
        if not os.path.exists(self.test_pdf_path):
            self.skipTest("Sample PDF not found")

        results = extract_variables(self.test_pdf_path, DEFAULT_PATTERNS)
        self.assertTrue(any("test@email.com" in e for e in results["emails"]))
        self.assertTrue(any("123-456-7890" in p for p in results["phone_numbers"]))
        self.assertTrue(any("$100.00" in d for d in results["dollar_amounts"]))
        self.assertTrue(any("01/01/2023" in d for d in results["dates"]))

    def test_patterns_endpoint(self):
        resp = self.app.get("/patterns", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        for key in (b"emails", b"phone_numbers", b"dates", b"dollar_amounts"):
            self.assertIn(key, resp.data)


if __name__ == "__main__":
    unittest.main()

