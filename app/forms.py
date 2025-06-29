from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, URL, NumberRange, ValidationError
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class MarketForm(FlaskForm):
    title = StringField('Market Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    resolution_date = StringField('Resolution Date (YYYY-MM-DD)', validators=[DataRequired()])
    resolution_method = TextAreaField('Resolution Method', validators=[DataRequired()])
    source_name = StringField('News Source Name')
    source_url = StringField('News Source URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Create Market')

    def validate_resolution_date(self, field):
        try:
            # Try to parse the date using strict YYYY-MM-DD format
            datetime.strptime(field.data, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Please enter the date in YYYY-MM-DD format')

class PredictionForm(FlaskForm):
    outcome = StringField('Prediction', validators=[DataRequired()])
    points_staked = IntegerField('Points Staked', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Place Prediction')

class NewsSourceForm(FlaskForm):
    name = StringField('Source Name', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    selector = StringField('Headline Selector', validators=[DataRequired()])
    date_selector = StringField('Date Selector', validators=[DataRequired()])
    active = BooleanField('Active')
    domain_tag = StringField('Domain Tag', validators=[DataRequired()], 
        description='Category of news content (e.g., crime, infrastructure, weather)')
    source_weight = FloatField('Source Weight', validators=[NumberRange(min=0.0, max=1.0)], 
        description='Reliability weight (0.0 to 1.0)')
    submit = SubmitField('Save Source')

class LBForm(FlaskForm):
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')

class LeagueForm(FlaskForm):
    """Form for creating a new league"""
    name = StringField('League Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    min_xp = IntegerField('Minimum XP Required', validators=[NumberRange(min=0)])
    submit = SubmitField('Create League')
