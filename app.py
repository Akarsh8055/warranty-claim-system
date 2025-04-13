import os
import random
import string
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, send_file, jsonify
from werkzeug.utils import secure_filename
import uuid
from models import db, WarrantyClaim
import traceback
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Basic Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///warranty_claims.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

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

            # Debug log
            logger.debug(f"Received form data: {request.form}")

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
            uploaded_file = request.files.get('document')
            file_path = None

            if uploaded_file and uploaded_file.filename:
                if not allowed_file(uploaded_file.filename):
                    flash('Invalid file type. Please upload PDF, JPG, JPEG, PNG, DOC or DOCX files.', 'error')
                    return redirect(url_for('index'))

                try:
                    filename = secure_filename(uploaded_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                    # Save the file
                    uploaded_file.save(file_path)
                except Exception as e:
                    logger.error(f"File upload error: {str(e)}")
                    flash('Error uploading file. Please try again.', 'error')
                    return redirect(url_for('index'))

            # Generate reference number
            reference_number = generate_reference_number()

            try:
                # Create new warranty claim in the database
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

@app.route('/authorized/management/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')

        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid password. Please try again.', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/authorized/management/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))

@app.route('/authorized/management/admin/dashboard')
def admin():
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    # Get all claims
    claims = WarrantyClaim.query.order_by(WarrantyClaim.created_at.desc()).all()
    return render_template('admin.html', claims=claims)

@app.route('/authorized/management/admin/view/<int:claim_id>')
def view_claim(claim_id):
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    claim = WarrantyClaim.query.get_or_404(claim_id)
    return render_template('admin_view.html', claim=claim)

@app.route('/authorized/management/admin/download/<int:claim_id>')
def download_file(claim_id):
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    claim = WarrantyClaim.query.get_or_404(claim_id)
    if not claim.file_path:
        flash('No file attached to this claim.', 'error')
        return redirect(url_for('view_claim', claim_id=claim_id))

    return send_file(claim.file_path, as_attachment=True)

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

@app.route('/authorized/management/admin/approve/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return {'error': 'Unauthorized'}, 401

    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        claim.status = 'approved'
        claim.updated_at = datetime.now()
        db.session.commit()
        return {'message': 'Claim approved successfully'}, 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving claim: {str(e)}")
        return {'error': 'Failed to approve claim'}, 500

@app.route('/authorized/management/admin/reject/<int:claim_id>', methods=['POST'])
def reject_claim(claim_id):
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return {'error': 'Unauthorized'}, 401

    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        claim.status = 'rejected'
        claim.updated_at = datetime.now()
        db.session.commit()
        return {'message': 'Claim rejected successfully'}, 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting claim: {str(e)}")
        return {'error': 'Failed to reject claim'}, 500

@app.route('/claim/<int:claim_id>')
def get_claim_json(claim_id):
    # Check if user is authenticated
    if not session.get('admin_authenticated'):
        return {'error': 'Unauthorized'}, 401

    try:
        claim = WarrantyClaim.query.get_or_404(claim_id)
        return {
            'id': claim.id,
            'reference_number': claim.reference_number,
            'name': claim.name,
            'email': claim.email,
            'phone': claim.phone,
            'product': claim.product,
            'purchase_date': claim.purchase_date,
            'issue': claim.issue,
            'defect_reason': claim.defect_reason,
            'warranty_option': claim.warranty_option,
            'status': claim.status,
            'created_at': claim.created_at.isoformat(),
            'has_file': bool(claim.file_path)
        }
    except Exception as e:
        logger.error(f"Error fetching claim details: {str(e)}")
        return {'error': 'Failed to fetch claim details'}, 500

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