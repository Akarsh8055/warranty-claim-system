# Warranty Claim Management System

A Flask-based web application for managing warranty claims with an admin dashboard.

## Features

- User-friendly warranty claim submission form
- File upload support for claim documentation
- Admin dashboard for claim management
- Claim status tracking (Pending, Approved, Rejected)
- Secure admin authentication
- Export claims to CSV
- File attachment download capability

## Tech Stack

- Python 3.x
- Flask
- SQLAlchemy
- SQLite
- HTML/CSS
- JavaScript

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd warranty-claim-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

5. Initialize the database:
```bash
flask run
```

## Usage

1. Start the development server:
```bash
python app.py
```

2. Access the application:
- Main form: `http://localhost:5001/`
- Admin login: `http://localhost:5001/authorized/management/admin/login`

## Deployment

This application is configured for deployment on Render. See deployment instructions in the documentation.

## Project Structure

```
warranty-claim-system/
├── app.py              # Main application file
├── models.py           # Database models
├── requirements.txt    # Project dependencies
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
└── uploads/           # File upload directory
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 