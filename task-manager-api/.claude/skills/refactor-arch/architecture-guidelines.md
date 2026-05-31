# Guidelines de Arquitetura MVC

## Princípio Central

O padrão MVC divide responsabilidades em três camadas distintas. **Nenhuma camada deve invadir a responsabilidade da outra.**

---

## Camada: Model

### Responsabilidades
- Representar entidades do domínio (User, Product, Order, Task)
- Abstrair o acesso ao banco de dados (queries CRUD com parâmetros seguros)
- Validações básicas da entidade (campo obrigatório, tipo, formato)
- Definir relacionamentos entre entidades

### NÃO deve conter
- Referências a `request` ou `response` HTTP
- Lógica de formatação de resposta JSON
- Regras de negócio complexas envolvendo múltiplas entidades
- Código de notificação (email, SMS, push)
- Concatenação de strings para montar queries SQL

### Estrutura Python/Flask
```python
# models/produto_model.py
class ProdutoModel:
    @staticmethod
    def get_by_id(db, produto_id):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(db, nome, descricao, preco, estoque, categoria):
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(db, produto_id, nome, descricao, preco, estoque, categoria):
        cursor = db.cursor()
        cursor.execute(
            "UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
            (nome, descricao, preco, estoque, categoria, produto_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def delete(db, produto_id):
        cursor = db.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()
        return cursor.rowcount > 0
```

### Estrutura Node.js/Express
```javascript
// models/courseModel.js
class CourseModel {
    constructor(db) { this.db = db; }

    getById(id) {
        return new Promise((resolve, reject) => {
            this.db.get("SELECT * FROM courses WHERE id = ?", [id], (err, row) => {
                if (err) reject(err); else resolve(row);
            });
        });
    }

    create(title, price) {
        return new Promise((resolve, reject) => {
            this.db.run(
                "INSERT INTO courses (title, price, active) VALUES (?, ?, 1)",
                [title, price],
                function(err) { if (err) reject(err); else resolve(this.lastID); }
            );
        });
    }
}
module.exports = CourseModel;
```

---

## Camada: Controller

### Responsabilidades
- Receber e validar dados de entrada (params, body, query string)
- Chamar os models/services necessários
- Orquestrar o fluxo de operações de negócio
- Formatar e retornar a resposta HTTP

### NÃO deve conter
- Queries SQL diretas
- Acesso direto a variáveis de configuração
- Imports de módulos HTTP externos (use dependency injection)

### Estrutura Python/Flask
```python
# controllers/produto_controller.py
from flask import request, jsonify
from models.produto_model import ProdutoModel
from database import get_db

def listar_produtos():
    db = get_db()
    produtos = ProdutoModel.get_all(db)
    return jsonify({"dados": produtos, "sucesso": True}), 200

def criar_produto():
    dados = request.get_json()
    if not dados or "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if "preco" not in dados or dados["preco"] < 0:
        return jsonify({"erro": "Preço inválido"}), 400

    db = get_db()
    produto_id = ProdutoModel.create(
        db, dados["nome"], dados.get("descricao", ""),
        dados["preco"], dados.get("estoque", 0), dados.get("categoria", "geral")
    )
    return jsonify({"dados": {"id": produto_id}, "sucesso": True}), 201
```

### Estrutura Node.js/Express
```javascript
// controllers/checkoutController.js
const CourseModel = require('../models/courseModel');
const UserModel = require('../models/userModel');
const EnrollmentModel = require('../models/enrollmentModel');

class CheckoutController {
    constructor(db) {
        this.courses = new CourseModel(db);
        this.users = new UserModel(db);
        this.enrollments = new EnrollmentModel(db);
    }

    async checkout(req, res) {
        const { userName, email, password, courseId, cardNumber } = req.body;
        if (!userName || !email || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Missing required fields' });
        }
        const course = await this.courses.getById(courseId);
        if (!course) return res.status(404).json({ error: 'Course not found' });
        // ... orchestrate enrollment
        res.status(200).json({ message: 'Checkout successful' });
    }
}
module.exports = CheckoutController;
```

---

## Camada: Views / Routes

### Responsabilidades
- Definir URLs e métodos HTTP aceitos
- Conectar rotas ao controller correspondente
- Aplicar middlewares específicos de rota (auth, rate limit)

### NÃO deve conter
- Lógica de negócio
- Acesso ao banco de dados
- Validações complexas

### Estrutura Python/Flask (Blueprints)
```python
# views/produto_routes.py
from flask import Blueprint
from controllers import produto_controller

produto_bp = Blueprint('produtos', __name__)

produto_bp.add_url_rule('/produtos', 'listar', produto_controller.listar_produtos, methods=['GET'])
produto_bp.add_url_rule('/produtos', 'criar', produto_controller.criar_produto, methods=['POST'])
produto_bp.add_url_rule('/produtos/<int:id>', 'buscar', produto_controller.buscar_produto, methods=['GET'])
produto_bp.add_url_rule('/produtos/<int:id>', 'atualizar', produto_controller.atualizar_produto, methods=['PUT'])
produto_bp.add_url_rule('/produtos/<int:id>', 'deletar', produto_controller.deletar_produto, methods=['DELETE'])
```

### Estrutura Node.js/Express (Router)
```javascript
// routes/checkoutRoutes.js
const express = require('express');
const router = express.Router();
const CheckoutController = require('../controllers/checkoutController');

module.exports = (db) => {
    const ctrl = new CheckoutController(db);
    router.post('/', (req, res) => ctrl.checkout(req, res));
    return router;
};
```

---

## Config (Módulo Obrigatório)

Centraliza todas as configurações. Usa variáveis de ambiente.

### Python/Flask
```python
# config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    # NUNCA coloque chaves reais aqui como default
```

### Node.js
```javascript
// config/settings.js
module.exports = {
    port: parseInt(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    jwtSecret: process.env.JWT_SECRET || 'dev-secret-change-in-production',
    smtpUser: process.env.SMTP_USER || '',
    smtpPass: process.env.SMTP_PASS || '',
};
```

---

## Middleware de Erro Centralizado

### Python/Flask
```python
# middlewares/error_handler.py
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": "Requisição inválida"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        # NUNCA retorne detalhes internos em produção
        return jsonify({"erro": "Erro interno do servidor"}), 500
```

### Node.js/Express
```javascript
// middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    const message = process.env.NODE_ENV === 'production'
        ? 'Internal Server Error'
        : err.message;
    res.status(status).json({ error: message });
}
module.exports = errorHandler;
```

---

## Entry Point — Composition Root

O `app.py` / `app.js` deve apenas montar a aplicação, sem lógica própria.

### Python/Flask
```python
# app.py
from flask import Flask
from flask_cors import CORS
from config.settings import Config
from views.produto_routes import produto_bp
from views.usuario_routes import usuario_bp
from views.pedido_routes import pedido_bp
from middlewares.error_handler import register_error_handlers
from database import init_db

def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    init_db(app)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    register_error_handlers(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
```

### Node.js/Express
```javascript
// src/app.js
const express = require('express');
const settings = require('./config/settings');
const Database = require('./database');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

const db = new Database(settings.dbPath);
db.init();

app.use('/api/checkout', checkoutRoutes(db));
app.use('/api', reportRoutes(db));
app.use(errorHandler);

app.listen(settings.port, () => {
    console.log(`Server running on port ${settings.port}`);
});
```

---

## Estrutura de Diretórios Padrão

### Python/Flask
```
project/
├── app.py                    # entry point / composition root
├── database.py               # conexão com banco
├── requirements.txt
├── config/
│   └── settings.py           # todas as configs via env vars
├── models/
│   ├── produto_model.py      # um arquivo por entidade
│   └── usuario_model.py
├── controllers/
│   ├── produto_controller.py # um arquivo por domínio
│   └── usuario_controller.py
├── views/
│   ├── produto_routes.py     # apenas rotas, sem lógica
│   └── usuario_routes.py
└── middlewares/
    └── error_handler.py      # error handling centralizado
```

### Node.js/Express
```
project/
├── src/
│   ├── app.js                # entry point
│   ├── database.js           # conexão com banco
│   ├── config/
│   │   └── settings.js
│   ├── models/
│   │   ├── userModel.js
│   │   └── courseModel.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   └── reportController.js
│   ├── routes/
│   │   ├── checkoutRoutes.js
│   │   └── reportRoutes.js
│   └── middlewares/
│       └── errorHandler.js
└── package.json
```
