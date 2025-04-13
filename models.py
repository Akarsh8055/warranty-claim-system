from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class WarrantyClaim(db.Model):
    __tablename__ = 'warranty_claims'
    
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # Increased length for international numbers
    product = db.Column(db.String(200), nullable=False)  # Increased length for longer product names
    purchase_date = db.Column(db.String(10), nullable=False)  # Store as string 'YYYY-MM-DD'
    issue = db.Column(db.Text, nullable=False)
    defect_reason = db.Column(db.String(50), nullable=False)
    warranty_option = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')

    def __repr__(self):
        return f'<WarrantyClaim {self.reference_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'reference_number': self.reference_number,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'product': self.product,
            'purchase_date': self.purchase_date,
            'issue': self.issue,
            'defect_reason': self.defect_reason,
            'warranty_option': self.warranty_option,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status
        }
