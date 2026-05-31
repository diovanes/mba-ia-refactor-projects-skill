"""Controller de Tasks — lógica de negócio extraída das routes."""
import logging
from flask import request, jsonify
from datetime import datetime
from database import db
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']


def _serialize_task(t):
    """Serialização com overdue usando Task.is_overdue() — sem duplicação."""
    data = t.to_dict()
    data['overdue'] = t.is_overdue()  # usa método do model, sem duplicar lógica
    if t.user_id:
        # SQLAlchemy lazy load — já resolvido pelo relacionamento
        data['user_name'] = t.user.name if t.user else None
    if t.category_id:
        data['category_name'] = t.category.name if t.category else None
    return data


def list_tasks():
    tasks = Task.query.all()
    return jsonify([_serialize_task(t) for t in tasks]), 200


def get_task(task_id):
    task = db.session.get(Task, task_id)  # SQLAlchemy 2.0 — não usa .query.get()
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(_serialize_task(task)), 200


def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title', '')
    if not title or len(title) < 3:
        return jsonify({'error': 'Título deve ter no mínimo 3 caracteres'}), 400
    if len(title) > 200:
        return jsonify({'error': 'Título muito longo'}), 400

    status = data.get('status', 'pending')
    if status not in VALID_STATUSES:
        return jsonify({'error': f'Status inválido. Válidos: {VALID_STATUSES}'}), 400

    priority = data.get('priority', 3)
    if not isinstance(priority, int) or priority < 1 or priority > 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    user_id = data.get('user_id')
    if user_id and not db.session.get(User, user_id):
        return jsonify({'error': 'Usuário não encontrado'}), 404

    category_id = data.get('category_id')
    if category_id and not db.session.get(Category, category_id):
        return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id
    )

    due_date_str = data.get('due_date')
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: id=%s title=%s", task.id, task.title)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'title' in data:
        if len(data['title']) < 3 or len(data['title']) > 200:
            return jsonify({'error': 'Título inválido'}), 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return jsonify({'error': 'Status inválido'}), 400
        task.status = data['status']

    if 'priority' in data:
        if not isinstance(data['priority'], int) or not (1 <= data['priority'] <= 5):
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Formato de data inválido'}), 400
        else:
            task.due_date = None

    if 'tags' in data:
        task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

    task.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Task atualizada: id=%s", task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: id=%s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    query_str = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    q = Task.query
    if query_str:
        q = q.filter(db.or_(
            Task.title.like(f'%{query_str}%'),
            Task.description.like(f'%{query_str}%')
        ))
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))

    return jsonify([t.to_dict() for t in q.all()]), 200


def task_stats():
    total = Task.query.count()
    status_counts = {s: Task.query.filter_by(status=s).count() for s in VALID_STATUSES}
    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    return jsonify({
        'total': total,
        **status_counts,
        'overdue': overdue_count,
        'completion_rate': round((status_counts['done'] / total) * 100, 2) if total > 0 else 0
    }), 200
