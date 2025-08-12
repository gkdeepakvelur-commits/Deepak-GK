import os
import json
from functools import wraps
from io import BytesIO
from datetime import datetime
from flask import session, request, redirect, url_for, flash
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
from app import db
from models import AuditLog

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('Administrator access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def create_audit_log(action, table_name, record_id, old_values, new_values, ip_address):
    """Create an audit log entry"""
    try:
        audit_log = AuditLog(
            user_id=session.get('user_id'),
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str) if new_values else None,
            ip_address=ip_address
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error creating audit log: {e}")

def generate_pdf_report(students):
    """Generate PDF report for students"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    elements = []
    elements.append(Paragraph("Student Results Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Create table data
    data = [['Roll No', 'Name', 'Department', 'Semester', 'Total Marks', 'Percentage', 'Grade']]
    
    for student in students:
        data.append([
            student.roll_no,
            student.name,
            student.department or 'N/A',
            str(student.semester) if student.semester else 'N/A',
            str(student.calculate_total_marks()),
            f"{student.calculate_percentage():.2f}%",
            student.get_grade()
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Add timestamp
    elements.append(Spacer(1, 20))
    timestamp = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    elements.append(timestamp)
    
    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def export_to_excel(students):
    """Export students data to Excel"""
    data = []
    for student in students:
        student_data = {
            'Roll No': student.roll_no,
            'Name': student.name,
            'Email': student.email,
            'Phone': student.phone,
            'Date of Birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            'Department': student.department,
            'Semester': student.semester,
            'Admission Year': student.admission_year,
            'Total Marks': student.calculate_total_marks(),
            'Percentage': round(student.calculate_percentage(), 2),
            'Grade': student.get_grade()
        }
        
        # Add subject-wise marks
        for mark in student.marks:
            subject_key = f"{mark.subject.code} ({mark.exam_type})"
            student_data[subject_key] = mark.marks_obtained
        
        data.append(student_data)
    
    df = pd.DataFrame(data)
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Student Results', index=False)
    
    excel_content = buffer.getvalue()
    buffer.close()
    
    return excel_content

def validate_csv_headers(headers, expected_headers):
    """Validate CSV headers"""
    missing_headers = set(expected_headers) - set(headers)
    extra_headers = set(headers) - set(expected_headers)
    
    return {
        'valid': len(missing_headers) == 0,
        'missing': list(missing_headers),
        'extra': list(extra_headers)
    }

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def clean_phone_number(phone):
    """Clean and format phone number"""
    if not phone:
        return None
    # Remove all non-digit characters
    cleaned = ''.join(filter(str.isdigit, phone))
    # Add country code if missing
    if len(cleaned) == 10:
        cleaned = '91' + cleaned  # Assuming India
    return cleaned

def generate_student_id(department, year):
    """Generate unique student ID"""
    from models import Student
    dept_code = department[:3].upper() if department else 'GEN'
    year_suffix = str(year)[-2:] if year else '23'
    
    # Find the last student ID for this department and year
    prefix = f"{dept_code}{year_suffix}"
    last_student = Student.query.filter(
        Student.roll_no.like(f"{prefix}%")
    ).order_by(Student.roll_no.desc()).first()
    
    if last_student:
        try:
            last_number = int(last_student.roll_no[-4:])
            new_number = last_number + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:04d}"
