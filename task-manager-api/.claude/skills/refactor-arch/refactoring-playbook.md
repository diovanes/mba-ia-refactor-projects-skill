# Playbook de Refatoração — Padrões de Transformação

Cada padrão contém: problema detectado, código antes, código depois, e passos de transformação.

---

## PT-01: Corrigir SQL Injection → Queries Parametrizadas

**Anti-pattern:** AP-01 (SQL Injection)

### Antes (vulnerável)
```python
# Python — concatenação de strings
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO produtos (nome) VALUES ('" + nome + "')")
cursor.execute("WHERE email = '" + email + "' AND senha = '" + senha + "'")

# Query dinâmica com f-string
cursor.execute(f"SELECT * FROM usuarios WHERE email = '{email}'")
```

```javascript
// Node.js — template literal
db.run(`DELETE FROM users WHERE id = ${id}`)
db.get(`SELECT * FROM courses WHERE id = ${cid} AND active = 1`)
```

### Depois (seguro)
```python
# Python — parâmetros posicionais com ?
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
cursor.execute("WHERE email = ? AND senha = ?", (email, senha))
```

```javascript
// Node.js — parâmetros posicionais
db.run("DELETE FROM users WHERE id = ?", [id])
db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [courseId])
```

### Passos de transformação:
1. Identifique toda concatenação de string em chamadas `cursor.execute()` ou `db.run/get/all()`
2. Substitua a string concatenada por `?` para cada variável
3. Adicione um segundo argumento com a tupla/array dos valores
4. Valide que nenhum input do usuário ainda está sendo concatenado

---

## PT-02: Extrair Credenciais Hardcoded → Variáveis de Ambiente

**Anti-pattern:** AP-02 (Credenciais Hardcoded)

### Antes
```python
# Python — hardcoded
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PASS = "admin123"
API_KEY = "pk_live_1234567890abcdef"
```

```javascript
// Node.js — hardcoded em objeto
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
};
```

### Depois
```python
# Python — config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    PAYMENT_KEY = os.environ.get('PAYMENT_GATEWAY_KEY', '')
```

```javascript
// Node.js — config/settings.js
module.exports = {
    dbPass: process.env.DB_PASS || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    jwtSecret: process.env.JWT_SECRET || 'dev-secret-change-in-production',
};
```

### Passos de transformação:
1. Crie `config/settings.py` (ou `config/settings.js`)
2. Para cada credencial, substitua o valor literal por `os.environ.get('NOME_VAR', 'default')`
3. O default deve ser um valor fictício ou vazio — nunca uma credencial real
4. Atualize os imports em todos os arquivos que usavam a configuração diretamente
5. (Opcional) Crie um arquivo `.env.example` com as variáveis necessárias sem os valores reais

---

## PT-03: Quebrar God Class → Controllers + Models Separados

**Anti-pattern:** AP-03 (God Class)

### Antes
```javascript
// AppManager.js — uma classe que faz tudo
class AppManager {
    constructor() { this.db = new Database(); }
    initDb() { /* cria tabelas e insere seeds */ }
    setupRoutes(app) { /* define TODAS as rotas */ }
    // rotas contêm lógica de negócio, queries, validações...
}
```

### Depois
```javascript
// database.js — apenas conexão
class Database {
    constructor(path) { this.db = new sqlite3.Database(path); }
    init() { /* apenas CREATE TABLE */ }
}

// models/courseModel.js — apenas queries
class CourseModel { getById(id) {...} create(title, price) {...} }

// controllers/checkoutController.js — apenas fluxo
class CheckoutController {
    async checkout(req, res) {
        // valida input → chama model → retorna response
    }
}

// routes/checkoutRoutes.js — apenas mapeamento URL→controller
router.post('/api/checkout', (req, res) => ctrl.checkout(req, res));
```

### Passos de transformação:
1. Identifique os domínios existentes (ex: users, courses, enrollments, payments)
2. Para cada domínio, crie `models/<domain>Model.js` com as queries
3. Para cada fluxo de negócio, crie `controllers/<flow>Controller.js`
4. Crie `routes/<domain>Routes.js` com apenas o mapeamento URL → controller
5. Remova a God Class original
6. Atualize o `app.js` para usar os novos módulos

---

## PT-04: Corrigir Senha Plain Text → Hashing Seguro

**Anti-pattern:** AP-04 (Senha em Plain Text)

### Antes
```python
# Python — armazena e compara sem hash
def criar_usuario(nome, email, senha):
    cursor.execute("INSERT INTO usuarios (..., senha) VALUES (?, ?, ?)",
                   (nome, email, senha))  # senha literal!

def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?",
                   (email, senha))  # comparação plain text!
```

```javascript
// Node.js — "hash" falso
function badCrypto(pwd) {
    return Buffer.from(pwd).toString('base64').substring(0, 10);
}
```

### Depois
```python
# Python — usando hashlib (ou bcrypt se disponível)
import hashlib, os

def hash_senha(senha):
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((senha + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verificar_senha(senha, stored_hash):
    salt, hashed = stored_hash.split(':')
    return hashlib.sha256((senha + salt).encode()).hexdigest() == hashed

# Com bcrypt (recomendado para produção):
# import bcrypt
# hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
# bcrypt.checkpw(senha.encode(), hash)
```

```javascript
// Node.js — com bcrypt
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 10);
const match = await bcrypt.compare(password, storedHash);
```

### Passos de transformação:
1. Adicione a função de hash no model de usuário
2. Ao criar usuário, hash a senha antes de inserir no banco
3. Ao fazer login, use a função de verificação em vez de comparar strings
4. Se o banco já tem senhas plain text, documente a necessidade de migração

---

## PT-05: Corrigir N+1 Queries → JOIN ou Eager Loading

**Anti-pattern:** AP-07 (N+1 Queries)

### Antes
```python
# Python — N+1: uma query por pedido, depois por item, depois por produto
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for pedido in pedidos:
    itens = cursor.execute(
        "SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],)
    ).fetchall()
    for item in itens:
        produto = cursor.execute(
            "SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)
        ).fetchone()
```

### Depois
```python
# Python — JOIN único busca tudo de uma vez
def get_pedidos_com_itens(db):
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario,
               pr.nome as produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        ORDER BY p.id
    """)
    rows = cursor.fetchall()
    # agrupa resultados por pedido
    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid, "usuario_id": row["usuario_id"],
                "status": row["status"], "total": row["total"],
                "criado_em": row["criado_em"], "itens": []
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
```

```javascript
// Node.js — JOIN com Promise
getFinancialReport() {
    return new Promise((resolve, reject) => {
        this.db.all(`
            SELECT c.title, c.id,
                   u.name as student_name,
                   pay.amount, pay.status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments pay ON pay.enrollment_id = e.id
        `, [], (err, rows) => {
            if (err) return reject(err);
            // agrupa por curso
            const report = {};
            rows.forEach(row => {
                if (!report[row.id]) report[row.id] = { course: row.title, revenue: 0, students: [] };
                if (row.status === 'PAID') report[row.id].revenue += row.amount;
                if (row.student_name) report[row.id].students.push({ student: row.student_name, paid: row.amount || 0 });
            });
            resolve(Object.values(report));
        });
    });
}
```

### Passos de transformação:
1. Identifique loops com queries dentro (grep por `execute` ou `db.get/all` dentro de `for`)
2. Reescreva com JOIN adequado
3. Agrupe os resultados no código Python/JS em vez de no banco

---

## PT-06: Remover Estado Global Mutável → Módulos com Estado Local

**Anti-pattern:** AP-08 (Estado Global Mutável)

### Antes
```javascript
// utils.js — estado global
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    globalCache[key] = data;  // mutação global
}
module.exports = { globalCache, totalRevenue, logAndCache };
```

### Depois
```javascript
// services/cacheService.js — estado encapsulado
class CacheService {
    constructor() { this._store = {}; }
    set(key, value) { this._store[key] = value; }
    get(key) { return this._store[key]; }
    clear() { this._store = {}; }
}
module.exports = new CacheService(); // singleton, mas controlado
```

### Passos de transformação:
1. Identifique variáveis `let` ou globais mutadas por múltiplas funções
2. Encapsule em uma classe ou módulo com interface clara
3. Passe o serviço como dependência para quem precisar (Dependency Injection)
4. Se o cache era apenas para logs, considere removê-lo completamente

---

## PT-07: Resolver Callback Hell → Async/Await

**Anti-pattern:** AP-09 (Callback Hell)

### Antes
```javascript
// 4 níveis de callbacks aninhados
db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    db.get("SELECT id FROM users WHERE email = ?", [email], (err, user) => {
        db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
            db.run("INSERT INTO payments ...", [this.lastID, amount], function(err) {
                res.json({ msg: "Sucesso" });
            });
        });
    });
});
```

### Depois
```javascript
// Promisify o banco de dados
const { promisify } = require('util');
// ou usar 'sqlite' wrapper que retorna Promises nativas

async function checkout(courseId, email, amount) {
    const course = await db.get("SELECT * FROM courses WHERE id = ?", [courseId]);
    if (!course) throw new Error('Course not found');

    const user = await db.get("SELECT id FROM users WHERE email = ?", [email]);
    const userId = user ? user.id : await createUser(email);

    const { lastID: enrollmentId } = await db.run(
        "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, courseId]
    );
    await db.run(
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, 'PAID')",
        [enrollmentId, amount]
    );
    return { enrollmentId };
}
```

### Passos de transformação:
1. Envolva as funções do driver de banco em Promises (ou use um wrapper como `sqlite`)
2. Converta funções aninhadas em funções `async`
3. Substitua callbacks por `await`
4. Adicione try/catch no nível do controller para capturar erros

---

## PT-08: Atualizar APIs Deprecated → Versões Atuais

**Anti-pattern:** AP-13 (APIs Deprecated)

### Antes — SQLAlchemy 2.0 (Python)
```python
# Deprecated no SQLAlchemy 2.0
task = Task.query.get(task_id)
user = User.query.get(user_id)
```

### Depois — SQLAlchemy 2.0
```python
# Forma atual e suportada
task = db.session.get(Task, task_id)
user = db.session.get(User, user_id)
```

### Antes — Flask deprecated
```python
# Flask < 2.0
@app.before_first_request
def setup():
    db.create_all()
```

### Depois — Flask >= 2.0
```python
with app.app_context():
    db.create_all()
```

### Antes — Express.js
```javascript
// Express < 4
res.send(404);
req.param('id');
```

### Depois — Express.js >= 4
```javascript
res.status(404).send('Not found');
req.params.id;  // ou req.query.id, req.body.id
```

### Passos de transformação:
1. Execute grep por `Query.get(` em arquivos Python para encontrar usos deprecated
2. Substitua `Model.query.get(id)` por `db.session.get(Model, id)`
3. Verifique a versão do SQLAlchemy em `requirements.txt` — se >= 2.0, todos os `.query.get()` devem ser migrados
4. Para Node.js, verifique a versão do Express/sqlite3 e aplique as substituições correspondentes

---

## PT-09: Remover Informações Sensíveis das Respostas

**Anti-pattern:** AP-10 (Informações Sensíveis Expostas)

### Antes
```python
# Health check expõe configurações internas
return jsonify({
    "status": "ok",
    "db_path": "loja.db",
    "debug": True,
    "secret_key": "minha-chave-super-secreta-123"  # NUNCA!
})

# Usuário com senha na resposta
return jsonify({"dados": usuario})  # usuario inclui campo "senha"
```

### Depois
```python
# Health check seguro
return jsonify({
    "status": "ok",
    "database": "connected",
    "version": "1.0.0"
    # sem paths, configs ou secrets
})

# Serialização segura do usuário
def usuario_publico(usuario):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"]
        # sem "senha"!
    }
```

### Passos de transformação:
1. Revise todas as respostas `jsonify()` ou `res.json()` que incluem objetos de banco
2. Crie funções de serialização que explicitamente listam campos seguros
3. Remova campos: `senha`, `password`, `hash`, `secret`, `token`, `key`, `debug`, `db_path`
4. No health check, retorne apenas status e versão — nunca configuração interna

---

## PT-10: Centralizar Error Handling

**Anti-pattern:** AP-12 (Ausência de Error Handling Centralizado)

### Antes
```python
# Mesmo padrão repetido em 15+ funções
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500  # vaza detalhes internos

def criar_produto():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500  # repetido!
```

### Depois
```python
# middlewares/error_handler.py
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": "Requisição inválida", "detalhes": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.exception("Unhandled exception: %s", str(e))
        return jsonify({"erro": "Erro interno do servidor"}), 500

# controllers — limpos, sem try/except duplicado
def listar_produtos():
    produtos = ProdutoModel.get_all(get_db())
    return jsonify({"dados": produtos, "sucesso": True}), 200
```

### Passos de transformação:
1. Crie `middlewares/error_handler.py` com handlers para 400, 404, 500 e Exception genérico
2. Registre os handlers no `app.py` com `register_error_handlers(app)`
3. Nos controllers, remova os try/except genéricos — deixe as exceções propagar naturalmente
4. Mantenha try/except apenas quando precisar tratar erros específicos (ex: rollback de DB)
