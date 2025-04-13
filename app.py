import os
import random
import string
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_file, jsonify
from werkzeug.utils import secure_filename
import uuid
from models import db, WarrantyClaim
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import hmac
import time

# Load environment variables
load_dotenv()

# Configure logging
if os.environ.get('PRODUCTION'):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Basic Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warranty_claims.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('PRODUCTION', False)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Admin credentials from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'WarrantyClaim2024@Secure')

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_reference_number():
    """Generate a unique reference number for the warranty claim"""
    prefix = "WC"
    timestamp = datetime.now().strftime("%Y%m%d")
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_chars}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-claim', methods=['POST'])
def submit_claim():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            product = request.form.get('product')
            purchase_date = request.form.get('purchase_date')
            issue = request.form.get('issue')
            defect_reason = request.form.get('defect-reason')
            warranty_option = request.form.get('warranty-option')

            # Validate required fields
            if not all([name, email, phone, product, purchase_date, issue, defect_reason, warranty_option]):
                missing_fields = [field for field, value in {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'product': product,
                    'purchase_date': purchase_date,
                    'issue': issue,
                    'defect_reason': defect_reason,
                    'warranty_option': warranty_option
                }.items() if not value]
                flash(f'Required fields missing: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('index'))

            # Validate date format
            try:
                datetime.strptime(purchase_date, '%Y-%m-%d')
            except (ValueError, TypeError) as e:
                logger.error(f"Date validation error: {str(e)}")
                flash('Invalid purchase date format. Please use YYYY-MM-DD format.', 'error')
                return redirect(url_for('index'))

            # File upload handling
            uploaded_file = request.files.get('supporting_document')
            file_path = None

            if uploaded_file and uploaded_file.filename:
                if not allowed_file(uploaded_file.filename):
                    flash('Invalid file type. Please upload PDF, JPG, JPEG, PNG files.', 'error')
                    return redirect(url_for('index'))

                try:
                    filename = secure_filename(uploaded_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    uploaded_file.save(file_path)
                except Exception as e:
                    logger.error(f"File upload error: {str(e)}")
                    flash('Error uploading file. Please try again.', 'error')
                    return redirect(url_for('index'))

            # Generate reference number
            reference_number = generate_reference_number()

            try:
                # Create new warranty claim
                new_claim = WarrantyClaim(
                    reference_number=reference_number,
                    name=name,
                    email=email,
                    phone=phone,
                    product=product,
                    purchase_date=purchase_date,
                    issue=issue,
                    defect_reason=defect_reason,
                    warranty_option=warranty_option,
                    file_path=file_path,
                    status='pending'
                )

                # Add and commit to database
                db.session.add(new_claim)
                db.session.commit()

                # Store data in session for confirmation page
                session['reference_number'] = reference_number
                session['claim_id'] = new_claim.id
                session['submission_data'] = new_claim.to_dict()

                return redirect(url_for('confirmation'))

            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                db.session.rollback()
                flash('Database error occurred. Please try again.', 'error')
                return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"General error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/confirmation')
def confirmation():
    reference_number = session.get('reference_number')
    claim_id = session.get('claim_id')

    if not reference_number or not claim_id:
        flash('No claim submission found.', 'error')
        return redirect(url_for('index'))

    # Try to get the saved data from the session first for backward compatibility
    submission_data = session.get('submission_data')

    # If not in session, query the database
    if not submission_data:
        claim = WarrantyClaim.query.get(claim_id)
        if not claim:
            flash('Claim not found.', 'error')
            return redirect(url_for('index'))

        submission_data = {
            'name': claim.name,
            'email': claim.email,
            'phone': claim.phone,
            'product': claim.product,
            'purchase_date': claim.purchase_date,
            'issue': claim.issue,
            'defect_reason': claim.defect_reason,
            'warranty_option': claim.warranty_option,
            'file_path': claim.file_path,
            'timestamp': claim.created_at.isoformat(),
            'reference_number': claim.reference_number
        }

    return render_template('confirmation.html', reference_number=reference_number, data=submission_data)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    try:
        # Clear any existing sessions for security
        session.clear()
        
        if request.method == 'POST':
            # Get client IP for rate limiting
            client_ip = request.remote_addr
            
            # Check rate limiting (implement a simple in-memory rate limit)
            current_time = time.time()
            if hasattr(app, 'login_attempts'):
                # Clean up old attempts
                app.login_attempts = {ip: attempts for ip, attempts in app.login_attempts.items() 
                                   if current_time - attempts['timestamp'] < 300}  # 5 minutes window
                
                if client_ip in app.login_attempts:
                    if app.login_attempts[client_ip]['count'] >= 5:  # Max 5 attempts per 5 minutes
                        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                        flash('Too many login attempts. Please try again later.', 'error')
                        return render_template('admin_login.html'), 429
                    app.login_attempts[client_ip]['count'] += 1
                else:
                    app.login_attempts[client_ip] = {'count': 1, 'timestamp': current_time}
            else:
                app.login_attempts = {client_ip: {'count': 1, 'timestamp': current_time}}

            username = request.form.get('username')
            password = request.form.get('password')

            # Log attempt details (without sensitive info)
            logger.info(f"Login attempt from IP: {client_ip}")

            if not username or not password:
                logger.warning(f"Admin login attempt with missing credentials from IP: {client_ip}")
                flash('Please provide both username and password.', 'error')
                return render_template('admin_login.html'), 400

            # Get admin credentials from environment variables
            admin_username = os.environ.get('ADMIN_USERNAME')
            admin_password = os.environ.get('ADMIN_PASSWORD')

            # Check if environment variables are set
            if not admin_username or not admin_password:
                logger.error("Admin credentials not set in environment variables")
                flash('Server configuration error. Please contact administrator.', 'error')
                return render_template('admin_login.html'), 500

            # Constant time comparison to prevent timing attacks
            if hmac.compare_digest(str(username), str(admin_username)) and hmac.compare_digest(str(password), str(admin_password)):
                logger.info(f"Successful admin login from IP: {client_ip}")
                
                # Set session with additional security measures
                session['admin_authenticated'] = True
                session['admin_ip'] = client_ip
                session['admin_ua'] = request.user_agent.string
                session['last_activity'] = time.time()
                session.permanent = True
                app.permanent_session_lifetime = timedelta(hours=1)  # Session expires after 1 hour
                
                # Clear failed attempts for this IP
                if client_ip in app.login_attempts:
                    del app.login_attempts[client_ip]
                
                return redirect(url_for('admin_dashboard'))
            else:
                logger.warning(f"Failed admin login attempt from IP: {client_ip}")
                flash('Invalid username or password.', 'error')
                return render_template('admin_login.html'), 401

        return render_template('admin_login.html')

    except Exception as e:
        logger.error(f"Error during admin login: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('admin_login.html'), 500

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_login'))

@app.route('/authorized/management/admin/dashboard')
def admin_dashboard():
    try:
        # Check if user is authenticated
        if not session.get('admin_authenticated'):
            logger.warning("Unauthorized access attempt to admin dashboard")
            flash('Please login to access the admin dashboard.', 'error')
            return redirect(url_for('admin_login'))

        # Fetch all warranty claims from the database
        claims = WarrantyClaim.query.order_by(WarrantyClaim.created_at.desc()).all()
        
        # Convert claims to dictionary format
        claims_data = [claim.to_dict() for claim in claims]
        
        logger.info(f"Admin dashboard loaded successfully. Found {len(claims)} claims.")
        return render_template('admin.html', claims=claims_data)

    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred while loading the dashboard.', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/view/<int:claim_id>')
def view_claim(claim_id):
    try:
        if not session.get('admin_authenticated'):
            logger.warning(f"Unauthorized attempt to view claim {claim_id}")
            return jsonify({'error': 'Unauthorized access'}), 401

        claim = WarrantyClaim.query.get(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return jsonify({'error': 'Claim not found'}), 404

        claim_data = claim.to_dict()
        claim_data['has_file'] = bool(claim.file_path)
        logger.info(f"Successfully retrieved claim details for ID: {claim_id}")
        return jsonify(claim_data)

    except Exception as e:
        logger.error(f"Error viewing claim {claim_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to retrieve claim details'}), 500

@app.route('/admin/download/<int:claim_id>')
def download_file(claim_id):
    try:
        if not session.get('admin_authenticated'):
            logger.warning(f"Unauthorized attempt to download file for claim {claim_id}")
            return "Unauthorized access", 401

        claim = WarrantyClaim.query.get(claim_id)
        if not claim or not claim.file_path:
            logger.error(f"File not found for claim: {claim_id}")
            return "File not found", 404

        if not os.path.exists(claim.file_path):
            logger.error(f"Physical file missing for claim {claim_id}: {claim.file_path}")
            return "File not found", 404

        logger.info(f"Downloading file for claim ID: {claim_id}")
        return send_file(
            claim.file_path,
            as_attachment=True,
            download_name=os.path.basename(claim.file_path)
        )

    except Exception as e:
        logger.error(f"Error downloading file for claim {claim_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return "Error downloading file", 500

@app.route('/admin/approve/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    try:
        if not session.get('admin_authenticated'):
            logger.warning(f"Unauthorized attempt to approve claim {claim_id}")
            return jsonify({'error': 'Unauthorized access'}), 401

        claim = WarrantyClaim.query.get(claim_id)
        if not claim:
            logger.error(f"Claim not found for approval: {claim_id}")
            return jsonify({'error': 'Claim not found'}), 404

        claim.status = 'approved'
        claim.updated_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Successfully approved claim {claim_id}")
        return jsonify({'message': 'Claim approved successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving claim {claim_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to approve claim'}), 500

@app.route('/admin/reject/<int:claim_id>', methods=['POST'])
def reject_claim(claim_id):
    try:
        if not session.get('admin_authenticated'):
            logger.warning(f"Unauthorized attempt to reject claim {claim_id}")
            return jsonify({'error': 'Unauthorized access'}), 401

        claim = WarrantyClaim.query.get(claim_id)
        if not claim:
            logger.error(f"Claim not found for rejection: {claim_id}")
            return jsonify({'error': 'Claim not found'}), 404

        claim.status = 'rejected'
        claim.updated_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Successfully rejected claim {claim_id}")
        return jsonify({'message': 'Claim rejected successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting claim {claim_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to reject claim'}), 500

@app.route('/authorized/management/admin/export')
def export_csv():
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    claims = WarrantyClaim.query.all()
    csv_data = "Reference Number,Name,Email,Phone,Product,Defect Reason,Warranty Option,Created At\n"
    
    for claim in claims:
        csv_data += f"{claim.reference_number},{claim.name},{claim.email},{claim.phone},{claim.product},{claim.defect_reason},{claim.warranty_option},{claim.created_at}\n"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=warranty_claims.csv"}
    )

@app.route('/test-email-template')
def test_email_template():
    # Sample data for testing
    test_data = {
        'name': 'Test Customer',
        'reference_number': 'WC-20240321-TEST123',
        'claim_details': {
            'product': 'Sample Product',
            'purchase_date': '2024-03-21',
            'issue': 'Test issue description',
            'defect_reason': 'manufacturing',
            'warranty_option': 'standard'
        }
    }
    
    return render_template(
        'email/confirmation.html',
        name=test_data['name'],
        reference_number=test_data['reference_number'],
        claim_details=test_data['claim_details']
    )

@app.route('/warranty-claim', methods=['GET', 'POST'])
def warranty_claim():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            product = request.form['product']
            purchase_date = request.form['purchase_date']
            issue = request.form['issue']
            defect_reason = request.form['defect_reason']
            warranty_option = request.form['warranty_option']
            
            # Handle file upload
            file = request.files.get('proof_file')
            file_path = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

            # Create warranty claim
            claim = WarrantyClaim(
                name=name,
                email=email,
                phone=phone,
                product=product,
                purchase_date=purchase_date,
                issue=issue,
                defect_reason=defect_reason,
                warranty_option=warranty_option,
                file_path=file_path
            )
            
            db.session.add(claim)
            db.session.commit()

            # Generate reference number
            reference_number = f"WC{claim.id:06d}"
            claim.reference_number = reference_number
            db.session.commit()

            return redirect(url_for('confirmation', reference=reference_number))

        except Exception as e:
            logger.error(f"Error processing warranty claim: {str(e)}")
            flash('An error occurred while processing your claim. Please try again.', 'error')
            return redirect(url_for('warranty_claim'))

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)