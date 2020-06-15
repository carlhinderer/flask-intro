from flask import Flask
from flask import abort, flash, make_response, redirect, render_template, request, session, url_for


# Initialize Template Extensions
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hardcoded-secret-key-for-dev'
bootstrap = Bootstrap(app)
moment = Moment(app)


# Initialize Database
import os
from flask_sqlalchemy import SQLAlchemy

db_url = 'postgresql://flaskexampleuser:flaskexamplepw@localhost/flaskexample'
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   
db = SQLAlchemy(app)


# Initialize Alembic Migrations
from flask_migrate import Migrate
migrate = Migrate(app, db)


# Initialize Mail
from flask_mail import Mail
mail = Mail(app)


# Model Definitions
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


# Form Definitions
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


# View Methods
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
        form=form, name=session.get('name'),
        known=session.get('known', False))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.route('/browser')
def browser():
    user_agent = request.headers.get('User-Agent')
    return '<p>Your browser is {}</p>'.format(user_agent)

@app.route('/bad')
def bad():
    return '</h1>Bad Request</h1>', 400

@app.route('/cookie')
def cookie():
    response = make_response('<h1>This document carries a cookie!</h1>')
    response.set_cookie('answer', '42')
    return response

@app.route('/cookies')
def cookies():
    return request.cookies

@app.route('/redirect')
def redirect_to_google():
    return redirect('http://www.google.com/')

@app.route('/abort')
def abort_404():
    abort(404)

@app.route('/diagnostic')
def diagnostic():
    print('Form:', request.form)
    print('Args:', request.args)
    print('Values:', request.values)
    print('Cookies:', request.cookies)
    print('Headers:', request.headers)
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# Shell Context Processor
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)