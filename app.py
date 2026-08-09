import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Models
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    age = db.Column(db.Integer)
    major = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills = db.relationship('UserSkill', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'age': self.age,
            'major': self.major,
            'skills': [skill.to_dict() for skill in self.skills]
        }

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('UserSkill', back_populates='skill')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class UserSkill(db.Model):
    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='skills')
    skill = db.relationship('Skill', back_populates='users')

    def to_dict(self):
        return {
            'skill': self.skill.to_dict() if self.skill else None,
            'proficiency_level': self.proficiency_level
        }

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    instructor = db.Column(db.String(255))
    skill_requirements = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    vector = db.relationship('CourseVector', back_populates='course', uselist=False, cascade='all, delete-orphan')

class CourseVector(db.Model):
    __tablename__ = 'course_vectors'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    embedding_vector = db.Column(db.ARRAY(db.Float))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = db.relationship('Course', back_populates='vector')

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/profile')
def profile_page():
    return render_template('profile.html')

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict(flat=True)
        skills_value = data.get('skills', '[]')
        try:
            data['skills'] = json.loads(skills_value)
        except (ValueError, TypeError):
            data['skills'] = []

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    age = data.get('age')
    major = data.get('major')
    skills = data.get('skills', [])

    if not username or not email or not password:
        return jsonify({'error': 'username, email, and password are required'}), 400

    try:
        age_value = int(age) if age is not None and age != '' else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Age must be an integer'}), 400

    if age_value is not None and (age_value < 10 or age_value > 110):
        return jsonify({'error': 'Age must be between 10 and 110'}), 400

    if phone:
        if not phone.isdigit() or len(phone) != 10:
            return jsonify({'error': 'Phone number must contain exactly 10 digits'}), 400

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': 'Email must include @ and a domain suffix like .com or .net'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email address is already registered'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken'}), 400

    user = User(username=username, email=email, phone=phone, age=age, major=major)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    for skill_payload in skills:
        skill_name = skill_payload.get('name')
        proficiency_level = skill_payload.get('proficiency_level', 'beginner')
        if not skill_name:
            continue

        skill = Skill.query.filter_by(name=skill_name).first()
        if not skill:
            skill = Skill(name=skill_name, description=skill_payload.get('description', ''))
            db.session.add(skill)
            db.session.flush()

        user_skill = UserSkill(user_id=user.id, skill_id=skill.id, proficiency_level=proficiency_level)
        db.session.add(user_skill)

    db.session.commit()
    token = create_access_token(identity=str(user.id))
    if request.is_json:
        return jsonify({'user': {'id': user.id, 'username': user.username, 'email': user.email}, 'token': token}), 201
    return redirect('/register-success')

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict(flat=True)

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.id))
    if request.is_json:
        return jsonify({'user': {'id': user.id, 'username': user.username, 'email': user.email}, 'token': token})
    return redirect('/login-success')

@app.route('/login-success')
def login_success():
    return render_template('login_success.html')

@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    try:
        user = User.query.get(int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid user identity'}), 422

    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()})

if __name__ == '__main__':
    app.run(debug=True)
