# Catálogo de Anti-Patterns — Auditoria Arquitetural

Cada anti-pattern contém: sinais de detecção, severidade, impacto e como verificar no código.

---

## AP-01: SQL Injection
**Severidade:** CRITICAL

### Sinais de detecção:
- Concatenação de strings para montar queries SQL
- Input do usuário diretamente inserido em queries
- Ausência de parâmetros `?` ou `:param` nas queries

### Como detectar (grep por):
```
Python: cursor.execute("... " + variavel)
Python: cursor.execute(f"... {variavel}")
Python: cursor.execute("SELECT ... WHERE campo = '" + campo + "'")
Node.js: db.run("SELECT ... WHERE id = " + id)
Node.js: db.query(`SELECT ... WHERE email = '${email}'`)
```

### Impacto:
Permite que atacantes leiam, modifiquem ou deletem dados do banco. Pode comprometer toda a aplicação.

---

## AP-02: Credenciais Hardcoded
**Severidade:** CRITICAL

### Sinais de detecção:
- SECRET_KEY, API_KEY, PASSWORD, TOKEN com valor literal no código
- Strings de conexão com usuário e senha no código
- Chaves de API de serviços externos (payment gateway, SMTP, etc.)

### Como detectar (procure por):
```python
# Python
SECRET_KEY = "valor-literal"
DB_PASSWORD = "senha123"
API_KEY = "pk_live_..."
```
```javascript
// Node.js
const config = { dbPass: "senha_prod_123", paymentKey: "pk_live_..." }
```

### Impacto:
Exposição de credenciais ao vazar código-fonte (GitHub, logs, etc.). Permite acesso não autorizado a sistemas externos.

---

## AP-03: God Class / God Method
**Severidade:** CRITICAL

### Sinais de detecção:
- Arquivo ou classe com mais de 300 linhas
- Uma única classe/arquivo contendo: rotas HTTP + queries SQL + lógica de negócio + validação + formatação
- Classe com mais de 10 métodos públicos de responsabilidades diferentes

### Como detectar:
- Arquivo com imports de módulos HTTP, banco de dados, e regras de negócio ao mesmo tempo
- Método com mais de 50 linhas
- Classe com nomes de métodos de domínios diferentes (ex: `processPayment()` e `sendEmail()` na mesma classe)

### Impacto:
Impossível testar em isolamento. Qualquer mudança pode quebrar partes não relacionadas. Alta probabilidade de bugs.

---

## AP-04: Senha em Plain Text
**Severidade:** CRITICAL

### Sinais de detecção:
- Senha armazenada no banco sem hashing
- Comparação direta de senha com string armazenada
- Ausência de `bcrypt`, `hashlib`, `argon2`, `scrypt`, ou `PBKDF2`

### Como detectar:
```python
# Python — vulnerável
cursor.execute("INSERT INTO usuarios (..., senha) VALUES ('" + senha + "')")
cursor.execute("SELECT ... WHERE senha = '" + senha + "'")
```
```javascript
// Node.js — hash falso
function badCrypto(pwd) { return Buffer.from(pwd).toString('base64') }
```

### Impacto:
Em caso de vazamento do banco, todas as senhas dos usuários ficam expostas. Viola LGPD/GDPR.

---

## AP-05: Endpoint Administrativo sem Autenticação
**Severidade:** CRITICAL

### Sinais de detecção:
- Rotas `/admin/*` sem middleware de autenticação
- Endpoint que executa queries SQL arbitrárias recebidas do request
- Endpoint que deleta/reseta dados do banco diretamente

### Como detectar:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = dados.get("sql", "")
    cursor.execute(query)  # executa qualquer SQL recebido!
```

### Impacto:
Acesso irrestrito ao banco de dados. Permite destruição total de dados por qualquer usuário.

---

## AP-06: Lógica de Negócio no Controller/Route
**Severidade:** HIGH

### Sinais de detecção:
- Cálculos de negócio (descontos, totais, regras) dentro de funções de rota
- Validações complexas de domínio diretamente nas routes
- Orquestração de múltiplos domínios dentro de uma única função de rota
- Controllers com mais de 30 linhas de lógica

### Como detectar:
```python
# Route fazendo cálculo de negócio — violação MVC
@app.route('/checkout', methods=['POST'])
def checkout():
    total = 0
    for item in itens:
        # lógica de desconto aqui — deveria estar no service/model
        if item['quantidade'] > 10:
            desconto = 0.1
        total += item['preco'] * item['quantidade'] * (1 - desconto)
```

### Impacto:
Impossível reutilizar e testar a lógica de negócio de forma isolada.

---

## AP-07: N+1 Queries
**Severidade:** HIGH

### Sinais de detecção:
- Query dentro de loop `for`
- Para cada item de uma lista, executa uma nova query ao banco
- Busca de dados relacionados item por item em vez de JOIN

### Como detectar:
```python
# Python — N+1 clássico
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for pedido in pedidos:
    # nova query para cada pedido!
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(pedido["id"])).fetchall()
    for item in itens:
        # mais uma query para cada item!
        produto = cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```

### Impacto:
Performance degradada exponencialmente com o crescimento dos dados. 100 pedidos = 100+ queries ao banco.

---

## AP-08: Estado Global Mutável
**Severidade:** HIGH

### Sinais de detecção:
- Variáveis globais que são modificadas por múltiplas funções
- Cache implementado como dicionário/objeto global
- Contadores globais atualizados em requests

### Como detectar:
```javascript
// Node.js — estado global
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    globalCache[key] = data;  // mutação de estado global
}
```

### Impacto:
Race conditions em servidores multi-thread/processo. Comportamento imprevisível. Impossível testar de forma isolada.

---

## AP-09: Callback Hell / Pyramid of Doom
**Severidade:** HIGH

### Sinais de detecção:
- Callbacks aninhados em mais de 3 níveis
- Indentação crescente formando uma pirâmide no código
- Difícil rastrear o fluxo de execução e tratamento de erros

### Como detectar:
```javascript
// Node.js — callback hell
db.get("SELECT ...", (err, result1) => {
    db.run("INSERT ...", (err, result2) => {
        db.run("INSERT ...", (err, result3) => {
            db.run("INSERT ...", (err, result4) => {
                // 4 níveis — ilegível e impossível de testar
            });
        });
    });
});
```

### Impacto:
Código ilegível, difícil de manter, propenso a erros de tratamento de exceções.

---

## AP-10: Informações Sensíveis Expostas em Response
**Severidade:** HIGH

### Sinais de detecção:
- SECRET_KEY, senha, token retornados em respostas da API
- Stack trace completo retornado ao cliente em produção
- Dados internos (path do banco, configuração de debug) no health check

### Como detectar:
```python
# Expõe SECRET_KEY na API!
return jsonify({
    "status": "ok",
    "secret_key": app.config["SECRET_KEY"],
    "debug": True
})
```

### Impacto:
Exposição de credenciais e informações de configuração que facilitam ataques.

---

## AP-11: Código Duplicado (DRY Violation)
**Severidade:** MEDIUM

### Sinais de detecção:
- Mesma lógica copiada em dois ou mais lugares
- Funções que diferem apenas em alguns parâmetros
- Mesma query SQL escrita múltiplas vezes

### Como detectar:
- Comparar funções `get_todos_pedidos()` e `get_pedidos_usuario()` — estrutura idêntica, apenas filtro diferente
- Bloco de validação de `priority` duplicado em create e update

### Impacto:
Bug em um lugar precisa ser corrigido em todos os lugares. Alta probabilidade de inconsistências.

---

## AP-12: Ausência de Tratamento de Erros Centralizado
**Severidade:** MEDIUM

### Sinais de detecção:
- try/except ou try/catch repetido em cada função
- Formato de erro diferente dependendo de qual parte do código falhou
- Erros não tratados que podem vazar stack traces ao usuário

### Como detectar:
```python
# Mesmo padrão repetido em 10+ funções
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500  # vaza detalhes internos
```

### Impacto:
Inconsistência nas respostas de erro. Código repetitivo. Stack traces vazados ao usuário.

---

## AP-13: APIs Deprecated
**Severidade:** MEDIUM

### Sinais de detecção:

#### SQLAlchemy 2.0 (Python)
- `Model.query.get(id)` → deprecated, use `db.session.get(Model, id)`
- `Query.first()` sem `limit(1)` → use `.limit(1).scalar()`

#### Node.js sqlite3 (callback API)
- Uso do driver `sqlite3` com callbacks em vez de `better-sqlite3` (síncrono) ou `sqlite` (promisified)
- API de callbacks em vez de Promises/async-await

#### Flask deprecated
- `before_first_request` → removido no Flask 2.3
- `flask.ext.*` → removido, use imports diretos

#### Express.js deprecated
- `res.send(404)` → use `res.status(404).send()`
- `req.param()` → use `req.params`, `req.query`, `req.body`

### Como detectar:
```python
# SQLAlchemy 2.0 — deprecated
task = Task.query.get(task_id)  # DeprecationWarning
user = User.query.get(user_id)  # DeprecationWarning
```
```javascript
// sqlite3 callback — legado
db.run("INSERT ...", (err) => { ... });  // prefira async/await
```

### Impacto:
Código quebrará em versões futuras. Warnings nos logs. Possíveis problemas de performance.

---

## AP-14: Nomes de Variáveis sem Significado
**Severidade:** LOW

### Sinais de detecção:
- Variáveis de uma letra: `u`, `e`, `p`, `c`, `d`
- Abreviações sem contexto: `cid`, `enrId`, `usr`, `pwd`
- Nomes genéricos: `data`, `temp`, `result` sem contexto

### Como detectar:
```javascript
let u = req.body.usr;    // u = user? username?
let e = req.body.eml;    // e = email?
let p = req.body.pwd;    // p = password?
let cid = req.body.c_id; // cid = courseId?
```

### Impacto:
Código ilegível. Dificulta manutenção e onboarding de novos desenvolvedores.

---

## AP-15: Magic Numbers e Strings
**Severidade:** LOW

### Sinais de detecção:
- Números literais em condicionais sem nome explicativo
- Strings de status/categoria repetidas literalmente no código
- Limites e thresholds sem constante nomeada

### Como detectar:
```python
if faturamento > 10000:    # por que 10000?
    desconto = faturamento * 0.1   # por que 0.1?
elif faturamento > 5000:
    desconto = faturamento * 0.05
```

### Impacto:
Difícil entender o significado dos valores. Mudança de regra de negócio requer busca por todos os lugares onde o valor aparece.

---

## AP-16: Bare Except / Catch-All Silencioso
**Severidade:** LOW

### Sinais de detecção:
- `except:` sem especificar o tipo de exceção (Python)
- `catch(e) {}` com bloco vazio (JavaScript)
- Captura de exceção sem log adequado

### Como detectar:
```python
try:
    task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
except:  # captura TUDO, incluindo KeyboardInterrupt, SystemExit
    return jsonify({'error': '...'}), 400
```

### Impacto:
Oculta bugs inesperados. Dificulta diagnóstico de problemas em produção.
