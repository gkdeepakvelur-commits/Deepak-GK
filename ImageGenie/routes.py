import os
import csv
import json
from datetime import datetime
from io import StringIO, BytesIO
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, asc, or_
from app import db
from models import User, Student, Subject, Mark, AuditLog, BulkOperation
from forms import LoginForm, StudentForm, SubjectForm, MarkForm, SearchForm
from utils import login_required, admin_required, allowed_file, create_audit_log, generate_pdf_report, export_to_excel

def register_routes(app):
    
    @app.route('/')
    def index():
        # Get basic statistics
        total_students = Student.query.filter_by(is_active=True).count()
        total_subjects = Subject.query.filter_by(is_active=True).count()
        total_marks = Mark.query.count()
        
        # Recent activities
        recent_students = Student.query.filter_by(is_active=True).order_by(desc(Student.created_at)).limit(5).all()
        recent_marks = Mark.query.order_by(desc(Mark.created_at)).limit(5).all()
        
        return render_template('index.html', 
                             total_students=total_students,
                             total_subjects=total_subjects,
                             total_marks=total_marks,
                             recent_students=recent_students,
                             recent_marks=recent_marks)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if session.get('user_id'):
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data) and user.is_active:
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                create_audit_log('LOGIN', 'users', user.id, None, None, request.remote_addr)
                flash('Login successful!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    def logout():
        if session.get('user_id'):
            create_audit_log('LOGOUT', 'users', session.get('user_id'), None, None, request.remote_addr)
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Advanced statistics for dashboard
        total_students = Student.query.filter_by(is_active=True).count()
        total_subjects = Subject.query.filter_by(is_active=True).count()
        total_marks = Mark.query.count()
        
        # Department-wise statistics
        dept_stats = db.session.query(
            Student.department,
            func.count(Student.id).label('count')
        ).filter(Student.is_active == True, Student.department.isnot(None)).group_by(Student.department).all()
        
        # Grade distribution
        grade_stats = {}
        students = Student.query.filter_by(is_active=True).all()
        for student in students:
            grade = student.get_grade()
            grade_stats[grade] = grade_stats.get(grade, 0) + 1
        
        # Top performers
        top_students = []
        for student in students:
            if student.marks:
                percentage = student.calculate_percentage()
                top_students.append({'student': student, 'percentage': percentage})
        top_students = sorted(top_students, key=lambda x: x['percentage'], reverse=True)[:10]
        
        # Recent activities
        recent_activities = AuditLog.query.order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        return render_template('dashboard.html',
                             total_students=total_students,
                             total_subjects=total_subjects,
                             total_marks=total_marks,
                             dept_stats=dept_stats,
                             grade_stats=grade_stats,
                             top_students=top_students,
                             recent_activities=recent_activities)
    
    @app.route('/students')
    @login_required
    def all_students():
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        department = request.args.get('department', '')
        semester = request.args.get('semester', '', type=str)
        
        query = Student.query.filter_by(is_active=True)
        
        if search:
            query = query.filter(
                or_(
                    Student.name.contains(search),
                    Student.roll_no.contains(search),
                    Student.email.contains(search)
                )
            )
        
        if department:
            query = query.filter(Student.department == department)
        
        if semester:
            query = query.filter(Student.semester == int(semester))
        
        students = query.order_by(Student.roll_no).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Get unique departments and semesters for filter
        departments = db.session.query(Student.department).filter(
            Student.department.isnot(None), Student.is_active == True
        ).distinct().all()
        semesters = db.session.query(Student.semester).filter(
            Student.semester.isnot(None), Student.is_active == True
        ).distinct().all()
        
        return render_template('all_students.html', 
                             students=students,
                             departments=[d[0] for d in departments],
                             semesters=[s[0] for s in semesters],
                             search=search,
                             current_department=department,
                             current_semester=semester)
    
    @app.route('/add_student', methods=['GET', 'POST'])
    @login_required
    def add_student():
        form = StudentForm()
        if form.validate_on_submit():
            student = Student(
                roll_no=form.roll_no.data,
                name=form.name.data,
                email=form.email.data or None,
                phone=form.phone.data or None,
                date_of_birth=form.date_of_birth.data,
                address=form.address.data or None,
                department=form.department.data or None,
                semester=form.semester.data,
                admission_year=form.admission_year.data
            )
            
            # Handle image upload
            if form.image.data:
                filename = secure_filename(f"{form.roll_no.data}_{form.image.data.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                form.image.data.save(filepath)
                student.image_filename = filename
            
            db.session.add(student)
            db.session.commit()
            
            create_audit_log('CREATE', 'students', student.id, None, student.__dict__, request.remote_addr)
            flash('Student added successfully!', 'success')
            return redirect(url_for('all_students'))
        
        return render_template('add_student.html', form=form)
    
    @app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
    @login_required
    def edit_student(student_id):
        student = Student.query.get_or_404(student_id)
        form = StudentForm(original_roll_no=student.roll_no, obj=student)
        
        if form.validate_on_submit():
            old_values = student.__dict__.copy()
            
            student.roll_no = form.roll_no.data
            student.name = form.name.data
            student.email = form.email.data or None
            student.phone = form.phone.data or None
            student.date_of_birth = form.date_of_birth.data
            student.address = form.address.data or None
            student.department = form.department.data or None
            student.semester = form.semester.data
            student.admission_year = form.admission_year.data
            student.updated_at = datetime.utcnow()
            
            # Handle image upload
            if form.image.data:
                # Remove old image if exists
                if student.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], student.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(f"{form.roll_no.data}_{form.image.data.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                form.image.data.save(filepath)
                student.image_filename = filename
            
            db.session.commit()
            
            create_audit_log('UPDATE', 'students', student.id, old_values, student.__dict__, request.remote_addr)
            flash('Student updated successfully!', 'success')
            return redirect(url_for('all_students'))
        
        return render_template('edit_student.html', form=form, student=student)
    
    @app.route('/delete_student/<int:student_id>', methods=['POST'])
    @admin_required
    def delete_student(student_id):
        student = Student.query.get_or_404(student_id)
        old_values = student.__dict__.copy()
        
        student.is_active = False
        student.updated_at = datetime.utcnow()
        db.session.commit()
        
        create_audit_log('DELETE', 'students', student.id, old_values, student.__dict__, request.remote_addr)
        flash(f'Student {student.name} has been deactivated.', 'success')
        return redirect(url_for('all_students'))
    
    @app.route('/subjects')
    @login_required
    def all_subjects():
        subjects = Subject.query.filter_by(is_active=True).order_by(Subject.code).all()
        return render_template('all_subjects.html', subjects=subjects)
    
    @app.route('/add_subject', methods=['GET', 'POST'])
    @admin_required
    def add_subject():
        form = SubjectForm()
        if form.validate_on_submit():
            subject = Subject(
                code=form.code.data,
                name=form.name.data,
                department=form.department.data or None,
                semester=form.semester.data,
                credits=form.credits.data
            )
            
            db.session.add(subject)
            db.session.commit()
            
            create_audit_log('CREATE', 'subjects', subject.id, None, subject.__dict__, request.remote_addr)
            flash('Subject added successfully!', 'success')
            return redirect(url_for('all_subjects'))
        
        return render_template('add_subject.html', form=form)
    
    @app.route('/add_marks', methods=['GET', 'POST'])
    @login_required
    def add_marks():
        form = MarkForm()
        if form.validate_on_submit():
            # Check if mark already exists for this combination
            existing_mark = Mark.query.filter_by(
                student_id=form.student_id.data,
                subject_id=form.subject_id.data,
                exam_type=form.exam_type.data
            ).first()
            
            if existing_mark:
                old_values = existing_mark.__dict__.copy()
                existing_mark.marks_obtained = form.marks_obtained.data
                existing_mark.total_marks = form.total_marks.data
                existing_mark.exam_date = form.exam_date.data
                existing_mark.updated_at = datetime.utcnow()
                
                create_audit_log('UPDATE', 'marks', existing_mark.id, old_values, existing_mark.__dict__, request.remote_addr)
                flash('Marks updated successfully!', 'success')
            else:
                mark = Mark(
                    student_id=form.student_id.data,
                    subject_id=form.subject_id.data,
                    marks_obtained=form.marks_obtained.data,
                    total_marks=form.total_marks.data,
                    exam_type=form.exam_type.data,
                    exam_date=form.exam_date.data
                )
                
                db.session.add(mark)
                create_audit_log('CREATE', 'marks', None, None, mark.__dict__, request.remote_addr)
                flash('Marks added successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('add_marks'))
        
        # Get all marks for display
        marks = Mark.query.join(Student).join(Subject).order_by(desc(Mark.created_at)).limit(20).all()
        
        return render_template('add_marks.html', form=form, marks=marks)
    
    @app.route('/search_result', methods=['GET', 'POST'])
    def search_result():
        form = SearchForm()
        student = None
        
        if form.validate_on_submit():
            student = Student.query.filter_by(
                roll_no=form.roll_no.data,
                is_active=True
            ).first()
            
            if student:
                # Verify date of birth if provided
                if form.date_of_birth.data:
                    if student.date_of_birth != form.date_of_birth.data:
                        flash('Date of birth does not match our records.', 'error')
                        student = None
                    else:
                        return redirect(url_for('view_result', roll_no=student.roll_no))
                else:
                    return redirect(url_for('view_result', roll_no=student.roll_no))
            else:
                flash('Student not found!', 'error')
        
        return render_template('search_result.html', form=form, student=student)
    
    @app.route('/view_result/<roll_no>')
    def view_result(roll_no):
        student = Student.query.filter_by(roll_no=roll_no, is_active=True).first_or_404()
        
        # Group marks by exam type
        marks_by_exam = {}
        for mark in student.marks:
            if mark.exam_type not in marks_by_exam:
                marks_by_exam[mark.exam_type] = []
            marks_by_exam[mark.exam_type].append(mark)
        
        return render_template('view_result.html', student=student, marks_by_exam=marks_by_exam)
    
    @app.route('/bulk_operations', methods=['GET', 'POST'])
    @admin_required
    def bulk_operations():
        if request.method == 'POST':
            operation = request.form.get('operation')
            
            if operation == 'import_students':
                return handle_import_students()
            elif operation == 'import_marks':
                return handle_import_marks()
            
        # Get recent bulk operations
        recent_operations = BulkOperation.query.order_by(desc(BulkOperation.created_at)).limit(10).all()
        
        return render_template('bulk_operations.html', recent_operations=recent_operations)
    
    def handle_import_students():
        if 'csv_file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(url_for('bulk_operations'))
        
        file = request.files['csv_file']
        if file.filename == '' or file.filename is None:
            flash('No file selected!', 'error')
            return redirect(url_for('bulk_operations'))
        
        if not (file.filename and file.filename.endswith('.csv')):
            flash('Please upload a CSV file!', 'error')
            return redirect(url_for('bulk_operations'))
        
        # Create bulk operation record
        bulk_op = BulkOperation(
            operation_type='import_students',
            user_id=session['user_id']
        )
        db.session.add(bulk_op)
        db.session.commit()
        
        try:
            # Read CSV file
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.reader(stream)
            
            skip_header = request.form.get('skip_header')
            if skip_header:
                next(csv_reader)  # Skip header row
            
            students_data = []
            errors = []
            line_number = 1 if not skip_header else 2
            
            for row in csv_reader:
                try:
                    if len(row) < 2:  # At least roll_no and name required
                        errors.append(f"Line {line_number}: Insufficient data")
                        continue
                    
                    roll_no = row[0].strip()
                    name = row[1].strip()
                    email = row[2].strip() if len(row) > 2 and row[2].strip() else None
                    phone = row[3].strip() if len(row) > 3 and row[3].strip() else None
                    
                    # Parse date of birth
                    dob = None
                    if len(row) > 4 and row[4].strip():
                        try:
                            dob = datetime.strptime(row[4].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Line {line_number}: Invalid date format for {roll_no}")
                            continue
                    
                    department = row[5].strip() if len(row) > 5 and row[5].strip() else None
                    semester = int(row[6]) if len(row) > 6 and row[6].strip().isdigit() else None
                    admission_year = int(row[7]) if len(row) > 7 and row[7].strip().isdigit() else None
                    address = row[8].strip() if len(row) > 8 and row[8].strip() else None
                    
                    # Check if student already exists
                    existing_student = Student.query.filter_by(roll_no=roll_no).first()
                    if existing_student:
                        errors.append(f"Line {line_number}: Student with roll number {roll_no} already exists")
                        continue
                    
                    students_data.append({
                        'roll_no': roll_no,
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'date_of_birth': dob,
                        'department': department,
                        'semester': semester,
                        'admission_year': admission_year,
                        'address': address
                    })
                    
                except Exception as e:
                    errors.append(f"Line {line_number}: {str(e)}")
                
                line_number += 1
            
            # Bulk insert students
            successful_imports = 0
            for student_data in students_data:
                try:
                    student = Student(**student_data)
                    db.session.add(student)
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Failed to import {student_data['roll_no']}: {str(e)}")
            
            # Update bulk operation
            bulk_op.total_records = len(students_data) + len(errors)
            bulk_op.processed_records = successful_imports
            bulk_op.failed_records = len(errors)
            bulk_op.status = 'completed'
            bulk_op.completed_at = datetime.utcnow()
            bulk_op.error_log = '\n'.join(errors) if errors else None
            
            db.session.commit()
            
            flash(f'Import completed! {successful_imports} students imported successfully. {len(errors)} errors.', 'success')
            if errors:
                flash(f'Errors encountered: {"; ".join(errors[:5])}{"..." if len(errors) > 5 else ""}', 'warning')
            
        except Exception as e:
            bulk_op.status = 'failed'
            bulk_op.error_log = str(e)
            db.session.commit()
            flash(f'Import failed: {str(e)}', 'error')
        
        return redirect(url_for('bulk_operations'))
    
    def handle_import_marks():
        if 'csv_file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(url_for('bulk_operations'))
        
        file = request.files['csv_file']
        if file.filename == '' or file.filename is None:
            flash('No file selected!', 'error')
            return redirect(url_for('bulk_operations'))
        
        if not (file.filename and file.filename.endswith('.csv')):
            flash('Please upload a CSV file!', 'error')
            return redirect(url_for('bulk_operations'))
        
        # Create bulk operation record
        bulk_op = BulkOperation(
            operation_type='import_marks',
            user_id=session['user_id']
        )
        db.session.add(bulk_op)
        db.session.commit()
        
        try:
            # Read CSV file
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.reader(stream)
            
            skip_header = request.form.get('skip_header')
            if skip_header:
                next(csv_reader)
            
            marks_data = []
            errors = []
            line_number = 1 if not skip_header else 2
            
            for row in csv_reader:
                try:
                    if len(row) < 4:  # At least roll_no, subject_code, marks_obtained, total_marks required
                        errors.append(f"Line {line_number}: Insufficient data")
                        continue
                    
                    roll_no = row[0].strip()
                    subject_code = row[1].strip()
                    marks_obtained = float(row[2])
                    total_marks = float(row[3])
                    exam_type = row[4].strip() if len(row) > 4 and row[4].strip() else 'Final'
                    
                    # Parse exam date
                    exam_date = None
                    if len(row) > 5 and row[5].strip():
                        try:
                            exam_date = datetime.strptime(row[5].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Line {line_number}: Invalid date format")
                            continue
                    
                    # Find student and subject
                    student = Student.query.filter_by(roll_no=roll_no).first()
                    if not student:
                        errors.append(f"Line {line_number}: Student {roll_no} not found")
                        continue
                    
                    subject = Subject.query.filter_by(code=subject_code).first()
                    if not subject:
                        errors.append(f"Line {line_number}: Subject {subject_code} not found")
                        continue
                    
                    marks_data.append({
                        'student_id': student.id,
                        'subject_id': subject.id,
                        'marks_obtained': marks_obtained,
                        'total_marks': total_marks,
                        'exam_type': exam_type,
                        'exam_date': exam_date
                    })
                    
                except Exception as e:
                    errors.append(f"Line {line_number}: {str(e)}")
                
                line_number += 1
            
            # Bulk insert marks
            successful_imports = 0
            for mark_data in marks_data:
                try:
                    # Check if mark already exists
                    existing_mark = Mark.query.filter_by(
                        student_id=mark_data['student_id'],
                        subject_id=mark_data['subject_id'],
                        exam_type=mark_data['exam_type']
                    ).first()
                    
                    if existing_mark:
                        # Update existing mark
                        existing_mark.marks_obtained = mark_data['marks_obtained']
                        existing_mark.total_marks = mark_data['total_marks']
                        existing_mark.exam_date = mark_data['exam_date']
                        existing_mark.updated_at = datetime.utcnow()
                    else:
                        # Create new mark
                        mark = Mark(**mark_data)
                        db.session.add(mark)
                    
                    successful_imports += 1
                except Exception as e:
                    errors.append(f"Failed to import mark: {str(e)}")
            
            # Update bulk operation
            bulk_op.total_records = len(marks_data) + len(errors)
            bulk_op.processed_records = successful_imports
            bulk_op.failed_records = len(errors)
            bulk_op.status = 'completed'
            bulk_op.completed_at = datetime.utcnow()
            bulk_op.error_log = '\n'.join(errors) if errors else None
            
            db.session.commit()
            
            flash(f'Import completed! {successful_imports} marks imported successfully. {len(errors)} errors.', 'success')
            if errors:
                flash(f'Errors encountered: {"; ".join(errors[:5])}{"..." if len(errors) > 5 else ""}', 'warning')
            
        except Exception as e:
            bulk_op.status = 'failed'
            bulk_op.error_log = str(e)
            db.session.commit()
            flash(f'Import failed: {str(e)}', 'error')
        
        return redirect(url_for('bulk_operations'))
    
    @app.route('/analytics')
    @login_required
    def analytics():
        # Performance analytics
        dept_performance = db.session.query(
            Student.department,
            func.avg(Mark.marks_obtained).label('avg_marks'),
            func.count(Mark.id).label('total_exams')
        ).join(Mark).filter(
            Student.is_active == True,
            Student.department.isnot(None)
        ).group_by(Student.department).all()
        
        # Subject-wise performance
        subject_performance = db.session.query(
            Subject.name,
            func.avg(Mark.marks_obtained).label('avg_marks'),
            func.count(Mark.id).label('total_exams')
        ).join(Mark).group_by(Subject.name).all()
        
        # Monthly trends - using PostgreSQL date functions
        monthly_trends = db.session.query(
            func.to_char(Mark.created_at, 'YYYY-MM').label('month'),
            func.avg(Mark.marks_obtained).label('avg_marks'),
            func.count(Mark.id).label('total_exams')
        ).group_by(func.to_char(Mark.created_at, 'YYYY-MM')).order_by('month').all()
        
        return render_template('analytics.html',
                             dept_performance=dept_performance,
                             subject_performance=subject_performance,
                             monthly_trends=monthly_trends)
    
    @app.route('/export_results/<format>')
    @admin_required
    def export_results(format):
        students = Student.query.filter_by(is_active=True).all()
        
        if format == 'pdf':
            pdf_content = generate_pdf_report(students)
            response = make_response(pdf_content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=student_results.pdf'
            return response
        elif format == 'excel':
            excel_content = export_to_excel(students)
            response = make_response(excel_content)
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = 'attachment; filename=student_results.xlsx'
            return response
        else:
            flash('Invalid export format!', 'error')
            return redirect(url_for('all_students'))
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
