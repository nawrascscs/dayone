from __future__ import annotations  # Must be the very first line!

import os
import re
from datetime import datetime
from typing import Any
from flask import Flask, jsonify, request, render_template, redirect
import json
from sqlalchemy import or_
from sqlalchemy.orm import Mapped
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Models ...

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Models
class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(120), unique=True, nullable=False)
    email: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = db.Column(db.String(255), nullable=False)
    phone: Mapped[str | None] = db.Column(db.String(50))
    age: Mapped[int | None] = db.Column(db.Integer)
    major: Mapped[str | None] = db.Column(db.String(120))
    created_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills: Mapped[list['UserSkill']] = db.relationship('UserSkill', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, username: str, email: str, password: str, phone: str | None = None, age: int | None = None, major: str | None = None) -> None:
        self.username = username
        self.email = email
        self.phone = phone
        self.age = age
        self.major = major
        self.set_password(password)

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

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(120), unique=True, nullable=False)
    description: Mapped[str | None] = db.Column(db.Text)
    created_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add this relationship
    users = db.relationship('UserSkill', back_populates='skill', cascade='all, delete-orphan')

    def __init__(self, name: str, description: str | None = None) -> None:
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class UserSkill(db.Model):
    __tablename__ = 'user_skills'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level: Mapped[str] = db.Column(db.String(50), nullable=False)
    created_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Fix indentation here
    user = db.relationship('User', back_populates='skills')
    skill = db.relationship('Skill', back_populates='users')

    def __init__(self, user_id: int, skill_id: int, proficiency_level: str) -> None:
        self.user_id = user_id
        self.skill_id = skill_id
        self.proficiency_level = proficiency_level

    def to_dict(self):
        return {
            'skill': self.skill.to_dict() if self.skill else None,
            'proficiency_level': self.proficiency_level
        }

class Course(db.Model):
    __tablename__ = 'courses'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    title: Mapped[str] = db.Column(db.String(255), nullable=False)
    description: Mapped[str | None] = db.Column(db.Text)
    instructor: Mapped[str | None] = db.Column(db.String(255))
    skill_requirements: Mapped[str | None] = db.Column(db.Text)
    created_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indent this line properly:
    vector = db.relationship('CourseVector', back_populates='course', uselist=False, cascade='all, delete-orphan')

    def __init__(self, title: str, description: str | None = None, instructor: str | None = None, skill_requirements: str | None = None) -> None:
        self.title = title
        self.description = description
        self.instructor = instructor
        self.skill_requirements = skill_requirements

    def to_dict(self):
        requirements = parse_skill_requirements(self.skill_requirements)
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'instructor': self.instructor,
            'skill_requirements': requirements,
            'skill_requirements_text': self.skill_requirements or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class CourseVector(db.Model):
    __tablename__ = 'course_vectors'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    course_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    embedding_vector: Mapped[list[float] | None] = db.Column(db.ARRAY(db.Float))
    created_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    course: Mapped['Course'] = db.relationship('Course', back_populates='vector')

    def __init__(self, course_id: int, embedding_vector: list[float] | None = None) -> None:
        self.course_id = course_id
        self.embedding_vector = embedding_vector


def parse_skill_requirements(text):
    if not text:
        return []
    parts = re.split(r'[;,\n]+', text)
    return [part.strip() for part in parts if part.strip()]


def get_user_skill_names(user):
    return {skill.skill.name.strip().lower() for skill in user.skills if skill.skill and skill.skill.name}


def score_course_for_user(course, user):
    requirements = {skill.strip().lower() for skill in parse_skill_requirements(course.skill_requirements)}
    if not requirements:
        return 0
    overlap = requirements.intersection(get_user_skill_names(user))
    return int(len(overlap) / len(requirements) * 100)


def build_course_payload(course, user=None):
    payload = course.to_dict()
    if user:
        payload['match_score'] = score_course_for_user(course, user)
    return payload


def query_courses_from_db(search_text=None, skill_filter=None):
    query = Course.query
    if search_text:
        pattern = f"%{search_text.strip()}%"
        query = query.filter(
            or_(
                Course.title.ilike(pattern),
                Course.description.ilike(pattern),
                Course.instructor.ilike(pattern)
            )
        )
    if skill_filter:
        skill_like = f"%{skill_filter.strip()}%"
        query = query.filter(Course.skill_requirements.ilike(skill_like))
    return query


def find_related_courses(course, limit=4):
    requirements = {skill.strip().lower() for skill in parse_skill_requirements(course.skill_requirements)}
    if not requirements:
        return []

    related = []
    for candidate in Course.query.filter(Course.id != course.id).all():
        candidate_skills = {skill.strip().lower() for skill in parse_skill_requirements(candidate.skill_requirements)}
        if not candidate_skills:
            continue
        common = requirements.intersection(candidate_skills)
        if common:
            related.append((len(common), candidate))
    related.sort(key=lambda item: item[0], reverse=True)
    return [candidate.to_dict() for _, candidate in related[:limit]]


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

@app.route('/courses')
def courses_page():
    return render_template('courses.html')

@app.route('/courses/<int:course_id>')
def course_detail_page(course_id):
    return render_template('course_detail.html', course_id=course_id)

@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html')

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data: dict[str, Any]
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
    country_code = data.get('country_code') or '1'
    age = data.get('age')
    major = data.get('major')
    skills = data.get('skills', [])

    if not username or not email or not password:
        return jsonify({'error': 'username, email, and password are required'}), 400

    if len(password) < 8 or len(password) > 12:
        return jsonify({'error': 'Password must be between 8 and 12 characters'}), 400
    if not re.search(r'[A-Z]', password) or not re.search(r'\d', password):
        return jsonify({'error': 'Password must include at least one uppercase letter and one number'}), 400

    try:
        age_value = int(age) if age is not None and age != '' else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Age must be an integer'}), 400

    if age_value is not None and (age_value < 10 or age_value > 105):
        return jsonify({'error': 'Age must be between 10 and 105'}), 400

    full_phone = None
    if phone:
        phone_digits = re.sub(r'\D', '', str(phone))
        if len(phone_digits) < 8 or len(phone_digits) > 12:
            return jsonify({'error': 'Phone number must contain between 8 and 12 digits'}), 400
        code_digits = re.sub(r'\D', '', str(country_code)) or '1'
        full_phone = f'+{code_digits}{phone_digits}'
        phone = full_phone

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': 'Email must include @ and a domain suffix like .com or .net'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email address is already registered'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken'}), 400

    user = User(username=username, email=email, phone=phone, age=age_value, major=major, password=password)
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

@app.route('/api/users/me', methods=['GET', 'PUT'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    try:
        user = User.query.get(int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid user identity'}), 422

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'PUT':
        data = request.get_json() or {}
        phone = data.get('phone')
        age = data.get('age')
        major = data.get('major')

        if phone and (not phone.isdigit() or len(phone) != 10):
            return jsonify({'error': 'Phone number must contain exactly 10 digits'}), 400
        if age is not None:
            try:
                age_value = int(age)
            except (TypeError, ValueError):
                return jsonify({'error': 'Age must be an integer'}), 400
            if age_value < 10 or age_value > 110:
                return jsonify({'error': 'Age must be between 10 and 110'}), 400
            user.age = age_value
        if major is not None:
            user.major = major
        if phone is not None:
            user.phone = phone

        db.session.commit()
        return jsonify({'user': user.to_dict()})

    return jsonify({'user': user.to_dict()})


@app.route('/api/courses', methods=['GET'])
def list_courses():
    search_text = request.args.get('q', '').strip()
    skill_filter = request.args.get('skill', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    user = None

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user = User.query.get(int(identity))
    except Exception:
        user = None

    query = query_courses_from_db(search_text, skill_filter)
    pagination = query.order_by(Course.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    courses = [build_course_payload(course, user) for course in pagination.items]
    return jsonify({
        'courses': courses,
        'page': page,
        'per_page': per_page,
        'total': pagination.total
    })


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    user = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user = User.query.get(int(identity))
    except Exception:
        user = None

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    course_data = build_course_payload(course, user)
    course_data['related_courses'] = find_related_courses(course)
    return jsonify({'course': course_data})


@app.route('/api/recommend', methods=['POST'])
@jwt_required()
def recommend_courses():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    requested_skills = request.get_json().get('skills', [])
    skill_names = {skill.get('name', '').strip().lower() for skill in requested_skills if skill.get('name')}
    if not skill_names:
        skill_names = get_user_skill_names(user)

    similar_courses = []
    for course in Course.query.all():
        requirements = {skill.strip().lower() for skill in parse_skill_requirements(course.skill_requirements)}
        if not requirements:
            continue
        matches = requirements.intersection(skill_names)
        score = int(len(matches) / len(requirements) * 100)
        similar_courses.append((score, course, matches))

    similar_courses.sort(key=lambda item: item[0], reverse=True)
    recommendations = [{
        **course.to_dict(),
        'match_score': score,
        'explanation': f"Matches your {', '.join(matches) if matches else 'core skills'}"
    } for score, course, matches in similar_courses[:8]]

    return jsonify({'recommendations': recommendations})


if __name__ == '__main__':
    app.run(debug=True)
