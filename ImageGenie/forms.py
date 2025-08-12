from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, FloatField, DateField, TextAreaField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from models import Student, Subject, User
from app import db

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class StudentForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(max=50)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    semester = IntegerField('Semester', validators=[Optional(), NumberRange(min=1, max=8)])
    admission_year = IntegerField('Admission Year', validators=[Optional(), NumberRange(min=2000, max=2030)])
    image = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    
    def __init__(self, original_roll_no=None, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.original_roll_no = original_roll_no
    
    def validate_roll_no(self, field):
        if field.data != self.original_roll_no:
            student = Student.query.filter_by(roll_no=field.data).first()
            if student:
                raise ValidationError('Roll number already exists.')
    
    def validate_email(self, field):
        if field.data:
            student = Student.query.filter_by(email=field.data).first()
            if student and (not self.original_roll_no or student.roll_no != self.original_roll_no):
                raise ValidationError('Email already registered.')

class SubjectForm(FlaskForm):
    code = StringField('Subject Code', validators=[DataRequired(), Length(max=20)])
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    semester = IntegerField('Semester', validators=[Optional(), NumberRange(min=1, max=8)])
    credits = IntegerField('Credits', validators=[DataRequired(), NumberRange(min=1, max=10)])
    
    def validate_code(self, field):
        subject = Subject.query.filter_by(code=field.data).first()
        if subject:
            raise ValidationError('Subject code already exists.')

class MarkForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired(), NumberRange(min=0)])
    total_marks = FloatField('Total Marks', validators=[DataRequired(), NumberRange(min=1)])
    exam_type = SelectField('Exam Type', choices=[
        ('Final', 'Final Exam'),
        ('Mid-term', 'Mid-term Exam'),
        ('Assignment', 'Assignment'),
        ('Quiz', 'Quiz'),
        ('Project', 'Project')
    ], validators=[DataRequired()])
    exam_date = DateField('Exam Date', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(MarkForm, self).__init__(*args, **kwargs)
        self.student_id.choices = [(s.id, f"{s.roll_no} - {s.name}") for s in Student.query.filter_by(is_active=True).order_by(Student.roll_no).all()]
        self.subject_id.choices = [(s.id, f"{s.code} - {s.name}") for s in Subject.query.filter_by(is_active=True).order_by(Subject.code).all()]
    
    def validate_marks_obtained(self, field):
        if field.data > self.total_marks.data:
            raise ValidationError('Marks obtained cannot be greater than total marks.')

class SearchForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
