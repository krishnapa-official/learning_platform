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

# ── Many-to-many table ─────────────────────────────────────
enrollments = db.Table('enrollments',
    db.Column('user_id',   db.Integer, db.ForeignKey('user.id'),   primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

# ── Models ─────────────────────────────────────────────────
class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    student_name = db.Column(db.String(100), nullable=True)
    email        = db.Column(db.String(120), nullable=True)
    phone        = db.Column(db.String(20),  nullable=True)
    courses      = db.relationship('Course', secondary=enrollments, backref='users')

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

# ── Create DB + Seed ───────────────────────────────────────
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

# ── Context Processor ──────────────────────────────────────
@app.context_processor
def inject_user():
    current_user = None
    enrolled_course_names = []
    if 'user' in session:
        current_user = User.query.filter_by(username=session['user']).first()
        if current_user:
            enrolled_course_names = [c.name for c in current_user.courses]
    return dict(
        current_user=current_user,
        enrolled_course_names=enrolled_course_names
    )

# ── Login Required Decorator ───────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Home ───────────────────────────────────────────────────
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

# ── About Pages ────────────────────────────────────────────
@app.route('/about')
def about():
    return redirect(url_for('ourstory'))

@app.route('/about/ourstory')
def ourstory():
    return render_template('ourstory.html')

@app.route('/about/mission')
def mission():
    return render_template('ourmission.html')

@app.route('/about/promise')
def promise():
    return render_template('ourpromise.html')

@app.route('/about/whatwedo')
def whatwedo():
    return render_template('whatwedo.html')

# ── Contact ────────────────────────────────────────────────
@app.route('/contact')
def contact():
    return render_template('contact.html')

# ── Courses ────────────────────────────────────────────────
@app.route('/courses')
def courses():
    return redirect(url_for('course_c'))

# ── Course Pages ───────────────────────────────────────────
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
    return render_template('SQL.html')

@app.route('/courses/datascience')
def course_datascience():
    return render_template('datascience.html')

# ── Register ───────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username     = request.form.get('username', '').strip()
        password     = request.form.get('password', '').strip()
        student_name = request.form.get('student_name', '').strip()
        email        = request.form.get('email', '').strip()
        phone        = request.form.get('phone', '').strip()
        subject      = request.form.get('subject', '').strip()

        if not username or not password or not subject:
            return render_template('register.html', error='All fields are required')
        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            student_name=student_name,
            email=email,
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()

        course = Course.query.filter_by(name=subject).first()
        if course:
            new_user.courses.append(course)
            db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

# ── Login ──────────────────────────────────────────────────
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

# ── Logout (handles both user and admin logout) ────────────
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))

# ── Admin Logout (separate route for admin nav links) ──────
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Admin logged out successfully", "info")
    return redirect(url_for('admin_login'))

# ── Enroll in Course (by name) ─────────────────────────────
@app.route('/enroll/<course_name>')
@login_required
def enroll_course(course_name):
    user = User.query.filter_by(username=session['user']).first()
    course = Course.query.filter_by(name=course_name).first()
    if user and course:
        if course not in user.courses:
            user.courses.append(course)
            db.session.commit()
            flash(f"Successfully enrolled in '{course.name}'!", "success")
        else:
            flash(f"You are already enrolled in '{course.name}'.", "info")
    return redirect(url_for('home'))

# ── Profile ────────────────────────────────────────────────
@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(username=session['user']).first()
    return render_template('profile.html', user=user)

# ── Admin Login ────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        if (request.form['username'] == ADMIN_USERNAME and
                request.form['password'] == ADMIN_PASSWORD):
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('adminlogin.html', error='Wrong username or password')
    return render_template('adminlogin.html')

# ── Admin Panel ────────────────────────────────────────────
@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    users = User.query.all()
    return render_template('admin.html', users=users)

# ── Admin Delete User ──────────────────────────────────────
@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def admin_delete(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    return redirect(url_for('admin_panel'))

# ── Admin Edit User ────────────────────────────────────────
@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    user    = User.query.get_or_404(user_id)
    courses = Course.query.all()
    if request.method == 'POST':
        new_username = request.form['username'].strip()
        new_password = request.form.get('password', '').strip()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return render_template('user.html', user=user, courses=courses,
                                   error='Username already taken.')
        user.username = new_username
        user.phone    = request.form.get('phone', '').strip()
        if new_password:
            user.password = generate_password_hash(new_password)
        course_id = request.form.get('course_id')
        user.courses.clear()
        if course_id:
            course = Course.query.get(int(course_id))
            if course:
                user.courses.append(course)
        db.session.commit()
        flash(f"User '{user.username}' updated successfully.", "success")
        return redirect(url_for('admin_panel'))
    return render_template('user.html', user=user, courses=courses)

# ── Admin Add User ─────────────────────────────────────────
@app.route('/admin/adduser', methods=['GET', 'POST'])
def admin_add_user():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
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
        return redirect(url_for('admin_panel'))
    return render_template('adduser.html', courses=Course.query.all())

# ── Admin Users Page ───────────────────────────────────────
@app.route('/admin/users')
def admin_users():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    users = User.query.options(db.joinedload(User.courses)).all()
    return render_template('admin_users.html', users=users)

# ── Admin Courses Page ─────────────────────────────────────
@app.route('/admin/courses')
def admin_courses():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    courses = Course.query.all()
    return render_template('admin_courses.html', courses=courses)

# ── Admin Settings ─────────────────────────────────────────
@app.route('/admin/settings')
def admin_settings():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_settings.html')

# ── Admin Dashboard ────────────────────────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_panel'))

# ── Admin Edit Course ──────────────────────────────────────
@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def admin_edit_course(course_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
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
        return redirect(url_for('admin_courses'))
    return render_template('admin_edit_course.html', course=course)

# ── Admin Enroll User ──────────────────────────────────────
@app.route('/admin/enroll/<int:user_id>', methods=['GET', 'POST'])
def admin_enroll(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    user    = User.query.get_or_404(user_id)
    courses = Course.query.all()
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        course = Course.query.get(course_id)
        if course and course not in user.courses:
            user.courses.append(course)
            db.session.commit()
            flash(f"'{user.username}' enrolled in '{course.name}'.", "success")
        return redirect(url_for('admin_users'))
    return render_template('admin_enroll.html', user=user, courses=courses)

# ── Admin Unenroll User ────────────────────────────────────
@app.route('/admin/unenroll/<int:user_id>/<int:course_id>', methods=['POST'])
def admin_unenroll(user_id, course_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    user   = User.query.get_or_404(user_id)
    course = Course.query.get_or_404(course_id)
    if course in user.courses:
        user.courses.remove(course)
        db.session.commit()
        flash(f"'{user.username}' unenrolled from '{course.name}'.", "success")
    return redirect(url_for('admin_users'))

# NEW
@app.route('/payment')
@login_required
def payment():
    course = request.args.get('course', '')
    return render_template('payment.html', preselected_course=course)

# ── Complete Enrollment ────────────────────────────────────
@app.route('/complete_enrollment', methods=['POST'])
@login_required
def complete_enrollment():
    course_name = request.form.get('course_name')
    user = User.query.filter_by(username=session['user']).first()
    course = Course.query.filter_by(name=course_name).first()
    if user and course:
        if course not in user.courses:
            user.courses.append(course)
            db.session.commit()
    return redirect(url_for('home'))
# ── ALWAYS LAST ────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)