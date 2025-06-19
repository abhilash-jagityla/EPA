# PDF Field Extractor

A secure web application that automatically extracts key business information from PDF documents. Built with Flask and designed for easy deployment on both Linux and Windows environments.

## Features

- 🔒 Secure user authentication system
- 📄 PDF document processing
- 🤖 Automatic field extraction
- 📊 CSV export functionality
- 🎯 Smart field detection
- 🖥️ Modern, responsive UI using Tailwind CSS
- 📱 Drag-and-drop file upload
- 💾 Secure file handling

## Extracted Fields

The application automatically extracts the following fields from PDF documents:
- Company Name
- Document Number
- Sold to Party
- Reference Number
- Total Net Value
- VAT Amount
- Total Due

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Virtual environment (recommended)
- Git

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd pdf-extractor
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the configuration:
```bash
# Create a .env file with the following content
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
UPLOAD_FOLDER=uploads
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:8000`

## Project Structure

```
pdf-extractor/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── models.py           # Database models
├── forms.py            # Form definitions
├── pdf_extractor.py    # PDF processing logic
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Landing page
│   ├── dashboard.html # Main upload interface
│   ├── results.html   # Results display
│   ├── login.html     # Login page
│   └── register.html  # Registration page
└── uploads/           # Temporary file storage
```

## Deployment

For detailed deployment instructions, see:
- [Linux Deployment Guide](LINUX_DEPLOYMENT.md)
- [Windows Deployment Guide](WINDOWS_DEPLOYMENT.md)

## Security Features

- User authentication with Flask-Login
- Secure password hashing
- CSRF protection
- Session management
- Secure file handling
- Input sanitization
- Rate limiting

## Field Detection

The application uses multiple strategies to detect fields:
1. Label-based detection (e.g., "Total Due:", "VAT Amount:")
2. Pattern matching for specific formats
3. Smart text cleaning and validation
4. Currency and number formatting

## Usage

1. Register an account or login
2. Navigate to the dashboard
3. Upload a PDF document (drag-and-drop supported)
4. View extracted fields on the results page
5. Download results as CSV

## Configuration

The application can be configured using environment variables:
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection string
- `UPLOAD_FOLDER`: Path for file uploads
- `MAX_CONTENT_LENGTH`: Maximum file size (default: 16MB)

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Check code coverage:
```bash
pytest --cov=.
```

## Troubleshooting

### Common Issues

1. PDF extraction fails:
   - Ensure PDF is not password protected
   - Check if PDF is text-based (not scanned)
   - Verify PDF is not corrupted

2. Field not detected:
   - Check if field format matches expected patterns
   - Verify text is properly formatted in PDF
   - Review field detection patterns in settings

3. Database errors:
   - Ensure database is properly initialized
   - Check database permissions
   - Verify connection settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support:
1. Check the documentation
2. Review troubleshooting guide
3. Open an issue on GitHub
4. Contact the development team

## Acknowledgments

- Flask framework
- PyMuPDF for PDF processing
- Tailwind CSS for UI
- Contributors and testers
