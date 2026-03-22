from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import uuid
import re
from werkzeug.utils import secure_filename
import os
import subprocess
import threading
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

ADMIN_EMAIL = 'this.pushpendra@gmail.com'

# Configuration: Use Render's persistent disk if available
DATA_DIR = os.environ.get('DATA_DIR', '.')
os.makedirs(DATA_DIR, exist_ok=True) # Ensure the directory exists

UPLOAD_FOLDER = os.path.join(DATA_DIR, 'user_upload')
REELS_DIR = os.path.join(DATA_DIR, 'reels')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webp'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get('SECRET_KEY', 'reelcraft-dev-secret-2025')

# Persistent Database Path - Using 4 slashes for absolute paths on Linux/Render
db_path = os.path.abspath(os.path.join(DATA_DIR, 'app.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"DEBUG: Database URI is {app.config['SQLALCHEMY_DATABASE_URI']}", flush=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default='User')
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    reels = db.relationship('Reel', backref='author', lazy=True)

class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PageVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(300), nullable=False)
    ip = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
with app.app_context():
    db.create_all()

# Ensure required directories exist at startup
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REELS_DIR, exist_ok=True)


# ── Background Worker Integration ──
def start_worker():
    from generate_process import run_worker
    worker_thread = threading.Thread(target=run_worker, args=(app, db, Reel), daemon=True)
    worker_thread.start()
    print("Background worker thread started.", flush=True)

# Start worker only if not in reload mode (optional, but cleaner)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    start_worker()


# ── Visit tracker middleware ──
@app.before_request
def track_visit():
    if request.path.startswith('/static') or request.path.startswith('/reels') or request.path == '/favicon.ico':
        return
    try:
        visit = PageVisit(
            path=request.path,
            ip=request.remote_addr,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(visit)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ── Admin access decorator ──
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.email != ADMIN_EMAIL:
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


UUID_PATTERN = re.compile(r'^[0-9a-zA-Z_-]+$')

def is_safe_uuid(value):
    return value and UUID_PATTERN.match(value.strip()) is not None


# ─────────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name', 'User')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email address already exists', 'error')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    myid = str(uuid.uuid1())
    if request.method == "POST":
        rec_id = request.form.get("uuid")
        desc = request.form.get("text", "").strip()
        audio_mode = request.form.get("audio_mode", "tts")

        if not rec_id or not is_safe_uuid(rec_id):
            flash("Invalid session. Please try again.", "error")
            return redirect(url_for("create"))

        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], rec_id.strip())
        os.makedirs(folder_path, exist_ok=True)

        input_files = []
        for key, file in request.files.items():
            if key == "music_file":
                continue
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(folder_path, filename))
                input_files.append(filename)

        if not input_files:
            flash("Please upload at least one image or video file.", "error")
            return redirect(url_for("create"))

        if audio_mode == "music":
            music_file = request.files.get("music_file")
            if music_file and music_file.filename:
                music_file.save(os.path.join(folder_path, "audio.mp3"))
            else:
                flash("Music mode selected but no MP3 file uploaded. Defaulting to silent reel.", "warning")
        else:
            with open(os.path.join(folder_path, "desc.txt"), "w", encoding="utf-8") as f:
                f.write(desc)

        abs_folder = os.path.abspath(folder_path)
        duration = 15 if len(input_files) == 1 else 3
        
        lines = []
        for fl in input_files:
            abs_path = os.path.join(abs_folder, fl).replace("\\", "/")
            lines.append(f"file '{abs_path}'\n")
            lines.append(f"duration {duration}\n")
            
        if input_files:
            last_path = os.path.join(abs_folder, input_files[-1]).replace("\\", "/")
            lines.append(f"file '{last_path}'\n")
            
        with open(os.path.join(folder_path, "input.txt"), "w", encoding="utf-8") as f:
            f.writelines(lines)

        new_reel = Reel(job_id=rec_id.strip(), user_id=current_user.id)
        db.session.add(new_reel)
        db.session.commit()

        flash("Your reel is being processed! We'll notify you when it's ready.", "success")
        return redirect(url_for("status", reel_id=rec_id))

    return render_template("create.html", myid=myid)


@app.route("/status/<reel_id>")
def status(reel_id):
    if not is_safe_uuid(reel_id):
        flash("Invalid reel ID.", "error")
        return redirect(url_for("home"))
    reel_record = Reel.query.filter_by(job_id=reel_id).first()
    is_done = reel_record is not None and reel_record.status == 'completed'
    reel_file = f"{reel_id}.mp4"

    return render_template("status.html",
                           reel_id=reel_id,
                           is_done=is_done,
                           reel_file=reel_file)


# Route to serve reels from the persistent storage
@app.route("/reels/<filename>")
def serve_reel(filename):
    return send_from_directory(REELS_DIR, filename)


@app.route("/gallery")
@login_required
def gallery():
    user_reels = Reel.query.filter_by(user_id=current_user.id).all()
    reels = []
    
    for r in user_reels:
        if os.path.exists(os.path.join(REELS_DIR, f"{r.job_id}.mp4")):
            reels.append(f"{r.job_id}.mp4")
            
    return render_template("gallery.html", reels=reels)


@app.route("/gallery/delete/<reel_id>", methods=["POST"])
@login_required
def delete_reel(reel_id):
    if not is_safe_uuid(reel_id):
        flash("Invalid reel ID.", "error")
        return redirect(url_for("gallery"))
        
    reel_record = Reel.query.filter_by(job_id=reel_id).first()
    if not reel_record or reel_record.user_id != current_user.id:
        flash("Reel not found or permission denied.", "error")
        return redirect(url_for("gallery"))

    db.session.delete(reel_record)
    db.session.commit()

    reel_path = os.path.join(REELS_DIR, f"{reel_id}.mp4")
    if os.path.isfile(reel_path):
        try:
            os.remove(reel_path)
            flash("Reel deleted from gallery.", "success")
        except OSError as e:
            flash(f"Could not delete reel: {e}", "error")
    else:
        flash("Reel not found.", "error")
    return redirect(url_for("gallery"))

@app.route('/admin')
@admin_required
def admin_dashboard():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = User.query.count()
    new_users_today = User.query.count()
    
    total_reels = Reel.query.count()
    completed_reels = Reel.query.filter_by(status='completed').count()
    pending_reels = Reel.query.filter(Reel.status != 'completed').count()

    total_visits = PageVisit.query.count()
    visits_today = PageVisit.query.filter(PageVisit.timestamp >= today_start).count()
    visits_week = PageVisit.query.filter(PageVisit.timestamp >= week_ago).count()
    visits_month = PageVisit.query.filter(PageVisit.timestamp >= month_ago).count()
    
    unique_visitors_today = db.session.query(db.func.count(db.distinct(PageVisit.ip))).filter(PageVisit.timestamp >= today_start).scalar()
    unique_visitors_total = db.session.query(db.func.count(db.distinct(PageVisit.ip))).scalar()

    top_pages = db.session.query(
        PageVisit.path,
        db.func.count(PageVisit.id).label('count')
    ).group_by(PageVisit.path).order_by(db.desc('count')).limit(10).all()

    recent_users = User.query.order_by(User.id.desc()).limit(10).all()
    
    user_reel_counts = db.session.query(
        User.name, User.email,
        db.func.count(Reel.id).label('reel_count')
    ).join(Reel, User.id == Reel.user_id).group_by(User.id).order_by(db.desc('reel_count')).limit(10).all()

    daily_visits = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = day + timedelta(days=1)
        count = PageVisit.query.filter(PageVisit.timestamp >= day, PageVisit.timestamp < next_day).count()
        daily_visits.append({'date': day.strftime('%b %d'), 'count': count})

    return render_template('admin.html',
        total_users=total_users,
        total_reels=total_reels,
        completed_reels=completed_reels,
        pending_reels=pending_reels,
        total_visits=total_visits,
        visits_today=visits_today,
        visits_week=visits_week,
        visits_month=visits_month,
        unique_visitors_today=unique_visitors_today,
        unique_visitors_total=unique_visitors_total,
        top_pages=top_pages,
        recent_users=recent_users,
        user_reel_counts=user_reel_counts,
        daily_visits=daily_visits
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
