from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class TicketForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    program_name = StringField('Program Name', validators=[DataRequired(), Length(max=100)])
    error_type = SelectField('Error Type', choices=[
        ('bug', 'Bug'),
        ('feature_request', 'Feature Request'),
        ('enhancement', 'Enhancement'),
        ('documentation', 'Documentation'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    attachment = FileField('Attachment')

class UpdateTicketForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed')
    ], validators=[DataRequired()])

class AdminProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Update Profile')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')