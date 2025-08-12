
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple authentication credentials (in a real app, use a database with hashed passwords)
ADMIN_CREDENTIALS = {
    'admin': 'password123',
    'kkcadmin': 'kkcedu12345'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

class Student:
    def __init__(self, roll_no, name, date_of_birth=None, image_filename=None):
        self.roll_no = roll_no
        self.name = name
        self.date_of_birth = date_of_birth
        self.image_filename = image_filename
        self.marks = {}

    def add_marks(self, subject, mark):
        self.marks[subject] = mark

    def calculate_total(self):
        return sum(self.marks.values())

    def calculate_percentage(self):
        if len(self.marks) == 0:
            return 0
        return (self.calculate_total() / len(self.marks))

    def to_dict(self):
        return {
            'roll_no': self.roll_no,
            'name': self.name,
            'date_of_birth': self.date_of_birth,
            'image_filename': self.image_filename,
            'marks': self.marks
        }

    @classmethod
    def from_dict(cls, data):
        student = cls(data['roll_no'], data['name'], data.get('date_of_birth'), data.get('image_filename'))
        student.marks = data['marks']
        return student

class StudentResultManagementSystem:
    def __init__(self):
        self.students = {}
        self.load_data()

    def save_data(self):
        data = {roll_no: student.to_dict() for roll_no, student in self.students.items()}
        with open('students_data.json', 'w') as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists('students_data.json'):
            try:
                with open('students_data.json', 'r') as f:
                    data = json.load(f)
                self.students = {roll_no: Student.from_dict(student_data) 
                               for roll_no, student_data in data.items()}
            except:
                self.students = {}

    def add_student(self, roll_no, name, date_of_birth=None, image_filename=None):
        self.students[roll_no] = Student(roll_no, name, date_of_birth, image_filename)
        self.save_data()

    def add_marks(self, roll_no, subject, mark):
        if roll_no in self.students:
            self.students[roll_no].add_marks(subject, mark)
            self.save_data()
            return True
        return False

    def get_student(self, roll_no):
        return self.students.get(roll_no)

    def search_by_name(self, name):
        for roll_no, student in self.students.items():
            if student.name.lower() == name.lower():
                return student
        return None

    def get_all_students(self):
        return list(self.students.values())

# Initialize the system
system = StudentResultManagementSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            
            # Redirect to the originally requested page or home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        
        if roll_no in system.students:
            flash('Student with this roll number already exists!', 'error')
        else:
            image_filename = None
            
            # Handle image upload if provided
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{roll_no}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_filename = filename
                elif file and file.filename != '' and not allowed_file(file.filename):
                    flash('Invalid file type! Please upload JPG or PNG images only.', 'error')
                    return render_template('add_student.html')
            
            system.add_student(roll_no, name, date_of_birth, image_filename)
            flash('Student added successfully!', 'success')
            return redirect(url_for('index'))
    
    return render_template('add_student.html')

@app.route('/add_marks', methods=['GET', 'POST'])
@login_required
def add_marks():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        subject = request.form['subject']
        mark = float(request.form['mark'])
        
        student = system.get_student(roll_no)
        if student:
            # Check if marks already exist for this subject
            if subject in student.marks:
                old_mark = student.marks[subject]
                system.add_marks(roll_no, subject, mark)
                flash(f'Marks updated successfully! {subject}: {old_mark} → {mark}', 'success')
            else:
                system.add_marks(roll_no, subject, mark)
                flash('Marks added successfully!', 'success')
        else:
            flash('Student not found!', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('add_marks.html', students=system.get_all_students())

@app.route('/view_result/<roll_no>')
def view_result(roll_no):
    student = system.get_student(roll_no)
    if student:
        return render_template('view_result.html', student=student)
    else:
        flash('Student not found!', 'error')
        return redirect(url_for('index'))

@app.route('/search_result', methods=['GET', 'POST'])
@login_required
def search_result():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        date_of_birth = request.form.get('date_of_birth', '').strip()
        
        student = system.get_student(roll_no)
        if student:
            # If date of birth is provided, verify it matches
            if date_of_birth and student.date_of_birth != date_of_birth:
                flash('Student found but date of birth does not match. Please verify the details.', 'error')
                return render_template('search_result.html')
            elif date_of_birth and not student.date_of_birth:
                flash('Student found but no date of birth on record. Displaying results.', 'warning')
            
            return render_template('view_result.html', student=student)
        else:
            flash('Student not found! Please check the roll number and try again.', 'error')
    
    return render_template('search_result.html')

@app.route('/view_result_by_roll', methods=['GET', 'POST'])
def view_result_by_roll():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        date_of_birth = request.form['date_of_birth']
        
        student = system.get_student(roll_no)
        if student:
            # Verify date of birth matches
            if student.date_of_birth and student.date_of_birth == date_of_birth:
                return render_template('view_result.html', student=student)
            elif not student.date_of_birth:
                flash('Student found but no date of birth on record. Please contact administration.', 'error')
            else:
                flash('Date of birth does not match our records. Please verify the details.', 'error')
        else:
            flash('Student not found! Please check the roll number.', 'error')
    
    return render_template('view_result_by_roll.html')

@app.route('/all_students')
@login_required
def all_students():
    students = system.get_all_students()
    return render_template('all_students.html', students=students)

@app.route('/edit_student/<roll_no>', methods=['GET', 'POST'])
@login_required
def edit_student(roll_no):
    student = system.get_student(roll_no)
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('all_students'))
    
    if request.method == 'POST':
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        
        # Update student details
        student.name = name
        student.date_of_birth = date_of_birth
        system.save_data()
        
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('all_students'))
    
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<roll_no>', methods=['POST'])
@login_required
def delete_student(roll_no):
    if roll_no in system.students:
        student_name = system.students[roll_no].name
        del system.students[roll_no]
        system.save_data()
        flash(f'Student {student_name} (Roll No: {roll_no}) has been deleted successfully!', 'success')
    else:
        flash('Student not found!', 'error')
    
    return redirect(url_for('all_students'))

@app.route('/delete_marks/<roll_no>/<subject>', methods=['POST'])
@login_required
def delete_marks(roll_no, subject):
    student = system.get_student(roll_no)
    if student and subject in student.marks:
        del student.marks[subject]
        system.save_data()
        flash(f'Marks for {subject} deleted successfully!', 'success')
    else:
        flash('Subject marks not found!', 'error')
    
    return redirect(url_for('add_marks'))

@app.route('/upload_image/<roll_no>', methods=['POST'])
@login_required
def upload_image(roll_no):
    student = system.get_student(roll_no)
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('all_students'))
    
    if 'image' not in request.files:
        flash('No image file selected!', 'error')
        return redirect(url_for('all_students'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No image file selected!', 'error')
        return redirect(url_for('all_students'))
    
    if file and allowed_file(file.filename):
        # Remove old image if exists
        if student.image_filename:
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], student.image_filename)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # Save new image
        filename = secure_filename(f"{roll_no}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Update student record
        student.image_filename = filename
        system.save_data()
        
        flash('Image uploaded successfully!', 'success')
    else:
        flash('Invalid file type! Please upload JPG or PNG images only.', 'error')
    
    return redirect(url_for('all_students'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
