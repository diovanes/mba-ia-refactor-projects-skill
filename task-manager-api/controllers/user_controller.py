"""Controller de Usuários — com hash seguro e sem senha no response."""
import logging
import re
from flask import request, jsonify
from database import db
from models.user import User
from models.task import Task

logger = logging.getLogger(__name__)

VALID_ROLES = ['user', 'admin', 'manager']
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


def get_user(user_id):
    user = db.session.get(User, user_id)  # SQLAlchemy 2.0
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return jsonify(data), 200


def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name', '')
    email = data.get('email', '')
    password = data.get('password', '')

    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400
    if not email or not EMAIL_REGEX.match(email):
        return jsonify({'error': 'Email inválido'}), 400
    if not password or len(password) < 4:
        return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'}), 400

    role = data.get('role', 'user')
    if role not in VALID_ROLES:
        return jsonify({'error': f'Role inválido. Válidos: {VALID_ROLES}'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: id=%s email=%s", user.id, user.email)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not EMAIL_REGEX.match(data['email']):
            return jsonify({'error': 'Email inválido'}), 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email já cadastrado'}), 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < 4:
            return jsonify({'error': 'Senha muito curta'}), 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    for task in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(task)

    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: id=%s", user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        result.append(data)
    return jsonify(result), 200


def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email', '')
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not user.active:
        return jsonify({'error': 'Usuário inativo'}), 403

    # TODO: implementar JWT real com PyJWT
    # import jwt; token = jwt.encode({'user_id': user.id}, Config.SECRET_KEY, algorithm='HS256')
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict()
    }), 200
