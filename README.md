# Warranty Claim Management System

A Flask-based web application for managing warranty claims with an admin dashboard.

## Features

- User-friendly warranty claim submission form
- File upload support for claim documentation
- Admin dashboard for claim management
- Claim approval/rejection functionality
- CSV export for claims data
- Email notification system
- Secure authentication for admin access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/warranty-claim-system.git
cd warranty-claim-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-admin-password
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url  # Required for production
```

5. Initialize the database:
```bash
flask db upgrade
```

## Running the Application

### Development
```bash
python app.py
```

### Production
```bash
gunicorn app:app
```

## Configuration

- `FLASK_ENV`: Set to 'development' or 'production'
- `SECRET_KEY`: Secret key for session management
- `ADMIN_USERNAME`: Admin panel username
- `ADMIN_PASSWORD`: Admin panel password
- `DATABASE_URL`: Database connection URL
- `REDIS_URL`: Redis connection URL (required for production)
- `UPLOAD_FOLDER`: Path for uploaded files

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 