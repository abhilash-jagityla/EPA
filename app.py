import os
import re
from datetime import datetime
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
import pandas as pd
import pdfplumber
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User
from forms import LoginForm, RegistrationForm
from pdf_extractor import PDFFieldExtractor

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_variables(pdf_path, patterns):
    results = {key: [] for key in patterns.keys()}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            for var_name, pattern in patterns.items():
                matches = re.finditer(pattern, text)
                for match in matches:
                    results[var_name].append(match.group())
    
    return results

# Common regex patterns
DEFAULT_PATTERNS = {
    'emails': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone_numbers': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'dates': r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',
    'dollar_amounts': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'files[]' not in request.files:
        flash('No files selected')
        return redirect(url_for('dashboard'))
    
    files = request.files.getlist('files[]')
    if not files or all(file.filename == '' for file in files):
        flash('No selected files')
        return redirect(url_for('dashboard'))
    
    # List to store all extracted data
    all_results = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Secure the filename and create unique name
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Save the uploaded file
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(pdf_path)
            
            try:
                # Process the PDF
                with PDFFieldExtractor(pdf_path) as extractor:
                    # Extract fields
                    fields = extractor.extract_fields()
                    
                    # Add filename to fields
                    fields['Source_File'] = filename
                    
                    # Add to results list
                    all_results.append(fields)
                    
                # Clean up the temporary file
                os.remove(pdf_path)
                    
            except Exception as e:
                flash(f'Error processing {filename}: {str(e)}')
                continue
        else:
            flash(f'Invalid file type for {file.filename}. Please upload only PDF files.')
    
    if not all_results:
        flash('No data could be extracted from the uploaded files.')
        return redirect(url_for('dashboard'))
    
    try:
        # Convert results to DataFrame
        df = pd.DataFrame(all_results)
        
        # Reorder columns to put Source_File first
        cols = ['Source_File'] + [col for col in df.columns if col != 'Source_File']
        df = df[cols]
        
        # Create Excel file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f'extracted_data_{timestamp}.xlsx'
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        
        # Create Excel writer with xlsxwriter engine for better formatting
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Extracted Data', index=False)
            
            # Get workbook and worksheet objects for formatting
            workbook = writer.book
            worksheet = writer.sheets['Extracted Data']
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D9EAD3',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)  # Set column width
        
        # Send the Excel file
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error creating Excel file: {str(e)}')
        return redirect(url_for('dashboard'))
    finally:
        # Clean up the Excel file after sending
        if 'excel_path' in locals() and os.path.exists(excel_path):
            os.remove(excel_path)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/patterns', methods=['GET'])
@login_required
def get_patterns():
    return jsonify(DEFAULT_PATTERNS)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True) 