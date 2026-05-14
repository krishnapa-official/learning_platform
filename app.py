import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = os.environ.get('SECRET_KEY', 'your-fixed-secret-key-change-this')

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

db = SQLAlchemy(app)

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Course(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    duration         = db.Column(db.String(50))
    schedule         = db.Column(db.String(50))
    instructor       = db.Column(db.String(100))
    mode             = db.Column(db.String(50))
    fee              = db.Column(db.Integer, default=0)
    registration_fee = db.Column(db.Integer, default=0)
    material_fee     = db.Column(db.Integer, default=0)
    discount         = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()
    if Course.query.count() == 0:
        seed = [
            Course(name="C",            duration="3 months", schedule="Mon/Wed/Fri", instructor="Mr. Rajan",    mode="Offline", fee=8000,  registration_fee=500,  material_fee=300, discount=0),
            Course(name="C++",          duration="3 months", schedule="Tue/Thu/Sat", instructor="Mr. Rajan",    mode="Offline", fee=8500,  registration_fee=500,  material_fee=300, discount=500),
            Course(name="Java",         duration="4 months", schedule="Mon/Wed/Fri", instructor="Ms. Priya",    mode="Online",  fee=10000, registration_fee=500,  material_fee=400, discount=1000),
            Course(name="SQL",          duration="2 months", schedule="Tue/Thu",     instructor="Mr. Arun",     mode="Online",  fee=6000,  registration_fee=500,  material_fee=200, discount=0),
            Course(name="Python",       duration="4 months", schedule="Mon/Wed/Fri", instructor="Ms. Priya",    mode="Online",  fee=10000, registration_fee=500,  material_fee=400, discount=1000),
            Course(name="Data Science", duration="6 months", schedule="Sat/Sun",     instructor="Dr. Sreejith", mode="Online",  fee=18000, registration_fee=1000, material_fee=500, discount=2000),
        ]
        db.session.add_all(seed)
        db.session.commit()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Home ──────────────────────────────────────────────────
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

# ── Course Pages ──────────────────────────────────────────
@app.route('/courses/c')
def course_c():
    return render_template('c.html')

@app.route('/courses/cpp')
def course_cpp():
    return render_template('cpp.html')

@app.route('/courses/java')
def course_java():
    return render_template('java.html')

@app.route('/courses/python')
def course_python():
    return render_template('python.html')

@app.route('/courses/sql')
def course_sql():
    return render_template('sql.html')

@app.route('/courses/datascience')
def course_datascience():
    return render_template('datascience.html')

# ── About Pages ───────────────────────────────────────────
@app.route('/about/ourstory')
def ourstory():
    return render_template('ourstory.html')

@app.route('/about/mission')
def mission():
    return render_template('mission.html')

@app.route('/about/promise')
def promise():
    return render_template('promise.html')

@app.route('/about/whatwedo')
def whatwedo():
    return render_template('whatwedo.html')

# ── Register ──────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='All fields are required')
        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        db.session.add(User(username=username, password=generate_password_hash(password)))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ── Login ─────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

# ── User Logout ───────────────────────────────────────────
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ── Admin Login ───────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect('/admin')
    if request.method == 'POST':
        if (request.form['username'] == ADMIN_USERNAME and
                request.form['password'] == ADMIN_PASSWORD):
            session['is_admin'] = True
            return redirect('/admin')
        return render_template('adminlogin.html', error='Wrong username or password')
    return render_template('adminlogin.html')

# ── Admin Panel ───────────────────────────────────────────
@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    users = User.query.all()
    return render_template('admin.html', users=users)

# ── Admin Delete ──────────────────────────────────────────
@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def admin_delete(user_id):
    if not session.get('is_admin'):
        return redirect('/admin/login')
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    return redirect('/admin')

# ── Admin Edit ────────────────────────────────────────────
@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit(user_id):
    if not session.get('is_admin'):
        return redirect('/admin/login')
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        new_username = request.form['username'].strip()
        new_password = request.form.get('password', '').strip()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return render_template('user.html', user=user, error='Username already taken.')
        user.username = new_username
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        flash(f"User '{user.username}' updated successfully.", "success")
        return redirect('/admin')
    return render_template('user.html', user=user)

# ── Admin Logout ──────────────────────────────────────────
@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

# ── Admin Add User ────────────────────────────────────────
@app.route('/admin/adduser', methods=['GET', 'POST'])
def admin_add_user():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    if request.method == 'POST':
        username  = request.form['username'].strip()
        password  = request.form['password'].strip()
        course_id = request.form.get('course_id', '').strip()
        if not username or not password:
            return render_template('adduser.html', error='Both fields are required.', courses=Course.query.all())
        if len(password) < 8:
            return render_template('adduser.html', error='Password must be at least 8 characters.', courses=Course.query.all())
        if User.query.filter_by(username=username).first():
            return render_template('adduser.html', error='Username already exists.', courses=Course.query.all())
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash(f"User '{username}' created successfully.", "success")
        return redirect('/admin')
    return render_template('adduser.html', courses=Course.query.all())

# ── Admin Users Page ──────────────────────────────────────
@app.route('/admin/users')
def admin_users():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# ── Admin Courses Page ────────────────────────────────────
@app.route('/admin/courses')
def admin_courses():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    courses = Course.query.all()
    return render_template('admin_courses.html', courses=courses)

# ── Admin Settings Page ───────────────────────────────────
@app.route('/admin/settings')
def admin_settings():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    return render_template('admin_settings.html')

# ── Admin Dashboard ───────────────────────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    return redirect('/admin')
    # ── Admin Edit Course ─────────────────────────────────────
@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def admin_edit_course(course_id):
    if not session.get('is_admin'):
        return redirect('/admin/login')
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.name             = request.form['name'].strip()
        course.duration         = request.form['duration'].strip()
        course.schedule         = request.form['schedule'].strip()
        course.instructor       = request.form['instructor'].strip()
        course.mode             = request.form['mode']
        course.fee              = int(request.form.get('fee', 0) or 0)
        course.registration_fee = int(request.form.get('registration_fee', 0) or 0)
        course.material_fee     = int(request.form.get('material_fee', 0) or 0)
        course.discount         = int(request.form.get('discount', 0) or 0)
        db.session.commit()
        flash(f"Course '{course.name}' updated successfully.", "success")
        return redirect('/admin/courses')
    return render_template('admin_edit_course.html', course=course)

# ── ALWAYS LAST ───────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)