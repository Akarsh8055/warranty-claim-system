import os
import random
import string
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from models import db, WarrantyClaim
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import hmac
import time
from flask_session import Session
import redis

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    static_url_path='',
    static_folder='static'
)

# Basic configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-123'),
    UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', 'uploads'),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB max file size
)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warranty_claims.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
if os.environ.get('FLASK_ENV') == 'production':
    try:
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            app.config['SESSION_TYPE'] = 'redis'
            app.config['SESSION_REDIS'] = redis.from_url(redis_url)
            logger.info("Using Redis for session storage")
        else:
            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
            logger.warning("Redis URL not set, using filesystem sessions")
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
else:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')

# Ensure upload and session directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
os.makedirs('static/css', exist_ok=True)

# Initialize extensions
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

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
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    uploaded_file.save(file_path)
                    app.logger.info(f'File saved successfully: {file_path}')
                except Exception as e:
                    app.logger.error(f'Error saving file: {str(e)}')
                    flash('Error saving file. Please try again.', 'error')
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
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            app.logger.info(f"Login attempt for username: {username}")
            
            if not username or not password:
                flash('Please enter both username and password', 'error')
                app.logger.warning("Login attempt with missing credentials")
                return redirect(url_for('admin_login'))
            
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                try:
                    session['admin_authenticated'] = True
                    session.permanent = True
                    app.logger.info("Admin login successful")
                    return redirect(url_for('admin_dashboard'))
                except Exception as e:
                    app.logger.error(f"Session error during login: {str(e)}")
                    flash('Session error. Please try again.', 'error')
                    return redirect(url_for('admin_login'))
            else:
                flash('Invalid username or password', 'error')
                app.logger.warning(f"Failed login attempt for username: {username}")
                return redirect(url_for('admin_login'))
                
        except Exception as e:
            app.logger.error(f"Error during admin login: {str(e)}")
            app.logger.error(traceback.format_exc())
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    try:
        session.clear()
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('admin_login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash('Error during logout.', 'error')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        if not session.get('admin_authenticated'):
            flash('Please login to access the admin dashboard.', 'error')
            app.logger.warning("Unauthorized access attempt to admin dashboard")
            return redirect(url_for('admin_login'))

        try:
            claims = WarrantyClaim.query.order_by(WarrantyClaim.created_at.desc()).all()
            app.logger.info(f"Successfully loaded {len(claims)} claims for admin dashboard")
            return render_template('admin.html', claims=claims)
        except Exception as e:
            app.logger.error(f"Database error in admin dashboard: {str(e)}")
            app.logger.error(traceback.format_exc())
            flash('Error loading claims data. Please try again.', 'error')
            return redirect(url_for('admin_login'))
            
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/view/<int:claim_id>')
def view_claim(claim_id):
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        return jsonify(claim.to_dict())
    except Exception as e:
        logger.error(f"Error viewing claim: {str(e)}")
        return jsonify({'error': 'Failed to load claim details'}), 500

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

@app.route('/authorized/management/admin/approve/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    if not session.get('admin_authenticated'):
        app.logger.warning(f'Unauthorized attempt to approve claim {claim_id}')
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 401
    
    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        if claim.status != 'pending':
            return jsonify({
                'success': False, 
                'error': f'Cannot approve claim that is already {claim.status}'
            }), 400
            
        claim.status = 'approved'
        db.session.commit()
        
        app.logger.info(f'Claim {claim_id} approved successfully')
        return jsonify({
            'success': True,
            'message': f'Claim {claim.reference_number} has been approved'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error approving claim {claim_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while approving the claim'
        }), 500

@app.route('/authorized/management/admin/reject/<int:claim_id>', methods=['POST'])
def reject_claim(claim_id):
    if not session.get('admin_authenticated'):
        app.logger.warning(f'Unauthorized attempt to reject claim {claim_id}')
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 401
    
    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        if claim.status != 'pending':
            return jsonify({
                'success': False, 
                'error': f'Cannot reject claim that is already {claim.status}'
            }), 400
            
        claim.status = 'rejected'
        db.session.commit()
        
        app.logger.info(f'Claim {claim_id} rejected successfully')
        return jsonify({
            'success': True,
            'message': f'Claim {claim.reference_number} has been rejected'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error rejecting claim {claim_id}: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while rejecting the claim'
        }), 500

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

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'redis': 'connected' if app.config['SESSION_TYPE'] == 'redis' else 'filesystem'
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Serve static files in production
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)