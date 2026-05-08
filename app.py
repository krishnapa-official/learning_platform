import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Flask App

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

db = SQLAlchemy(app)

# Database Model

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

# Create Database

with app.app_context():
    db.create_all()

# Login Required Function

def login_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if 'user' not in session:
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated

# Home Page

@app.route('/')
@app.route('/index')

def home():
    return render_template('index.html')

# Register Page

@app.route('/register', methods=['GET', 'POST'])

def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # Validation

        if not username or not password:

            return render_template(
                'register.html',
                error='All fields are required'
            )

        if len(password) < 8:

            return render_template(
                'register.html',
                error='Password must be at least 8 characters'
            )

        # Check Existing User

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            return render_template(
                'register.html',
                error='Username already exists'
            )

        # Save User

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Login Page

@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        # Check Password

        if user and check_password_hash(user.password, password):

            session['user'] = username

            # Redirect to Home Page
            return redirect(url_for('home'))

        else:

            return render_template(
                'login.html',
                error='Invalid username or password'
            )

    return render_template('login.html')

# Admin Page

@app.route('/admin')
@login_required

def admin():

    return render_template(
        'admin.html',
        username=session['user']
    )

# Logout

@app.route('/logout')

def logout():

    session.pop('user', None)

    return redirect(url_for('login'))

# Run App

if __name__ == '__main__':

    app.run(debug=True)