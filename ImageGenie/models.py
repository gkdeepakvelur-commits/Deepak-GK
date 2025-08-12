from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, teacher, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    admission_year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    marks = db.relationship('Mark', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def calculate_total_marks(self):
        return sum(mark.marks_obtained for mark in self.marks if mark.marks_obtained is not None)
    
    def calculate_percentage(self):
        if not self.marks:
            return 0
        total_marks = sum(mark.total_marks for mark in self.marks if mark.total_marks is not None)
        obtained_marks = sum(mark.marks_obtained for mark in self.marks if mark.marks_obtained is not None)
        return (obtained_marks / total_marks * 100) if total_marks > 0 else 0
    
    def get_grade(self):
        percentage = self.calculate_percentage()
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        else:
            return 'F'
    
    def __repr__(self):
        return f'<Student {self.roll_no}: {self.name}>'

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    credits = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    marks = db.relationship('Mark', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'

class Mark(db.Model):
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=True)
    total_marks = db.Column(db.Float, default=100.0)
    exam_type = db.Column(db.String(50), default='Final')  # Final, Mid-term, Assignment, etc.
    exam_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', 'exam_type', name='unique_student_subject_exam'),)
    
    def get_percentage(self):
        return (self.marks_obtained / self.total_marks * 100) if self.total_marks > 0 and self.marks_obtained is not None else 0
    
    def get_grade(self):
        percentage = self.get_percentage()
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        else:
            return 'F'
    
    def __repr__(self):
        return f'<Mark {self.student.roll_no} - {self.subject.code}: {self.marks_obtained}/{self.total_marks}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}>'

class BulkOperation(db.Model):
    __tablename__ = 'bulk_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False)  # import_students, import_marks, etc.
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    total_records = db.Column(db.Integer, default=0)
    processed_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)
    error_log = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='bulk_operations')
    
    def __repr__(self):
        return f'<BulkOperation {self.operation_type}: {self.status}>'
