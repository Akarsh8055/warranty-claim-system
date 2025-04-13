# Warranty Claim Management System

A web-based warranty claim management system built with Flask, featuring a user-friendly claim submission form and a secure admin panel for claim management.

## Features

- User-friendly warranty claim submission form
- Secure admin panel with login authentication
- Persistent storage of warranty claims
- File upload support for claim documentation
- Claim status management (approve/reject)
- Search and filter functionality
- Export claims to CSV
- Modern and responsive UI design

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd warranty-claim-project
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root and add the following:
```env
SECRET_KEY=your_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
DATABASE_URL=sqlite:///warranty_claims.db
UPLOAD_FOLDER=uploads
```

## Running the Application

### Development
```bash
python app.py
```
The application will be available at http://127.0.0.1:5001

### Production (Unix/Linux/MacOS)
```bash
gunicorn -c gunicorn_config.py app:app
```

Note: For Windows production deployment, consider using waitress or running on a Linux server with Gunicorn.

## Usage

1. **Submitting a Warranty Claim**
   - Visit http://127.0.0.1:5001
   - Fill out the warranty claim form
   - Upload supporting documents (optional)
   - Submit the claim

2. **Accessing Admin Panel**
   - Visit http://127.0.0.1:5001/admin/login
   - Login with admin credentials
   - View, approve, or reject claims
   - Search and filter claims
   - Export claims to CSV

## Directory Structure

```
warranty_claim_project/
├── app.py              # Main application file
├── models.py           # Database models
├── requirements.txt    # Project dependencies
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
├── uploads/           # Uploaded files
└── instance/          # Instance-specific files
```

## Security Features

- Session-based authentication
- Password protection for admin panel
- Rate limiting for login attempts
- Secure file upload handling
- CSRF protection
- XSS prevention
- SQL injection prevention through SQLAlchemy

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 