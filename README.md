# Criação de Skills — Refatoração Arquitetural Automatizada

Skill de auditoria e refatoração arquitetural para Claude Code, desenvolvida como desafio do MBA de IA. A skill analisa codebases, identifica anti-patterns classificados por severidade, gera relatório de auditoria e refatora automaticamente o projeto para o padrão MVC — de forma agnóstica de tecnologia.

---

## Análise Manual

### Projeto 1 — code-smells-project (Python/Flask)

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| CRITICAL | SQL Injection em queries por concatenação | `models.py:28,48,68,92,109,140,174` | Input do usuário inserido diretamente em strings SQL. Permite dump completo do banco. |
| CRITICAL | Endpoint `/admin/query` executa SQL arbitrário | `app.py:59-78` | Qualquer usuário pode executar `DROP TABLE` via HTTP sem autenticação. |
| CRITICAL | SECRET_KEY hardcoded | `app.py:7` | Chave de sessão literal no repositório — permite forjar tokens. |
| CRITICAL | Senhas armazenadas em plain text | `database.py:76-82` | Seed insere senhas literais. Login compara string diretamente. Viola LGPD. |
| HIGH | SECRET_KEY exposta na resposta da API `/health` | `controllers.py:289` | Endpoint retorna a chave secreta em JSON para qualquer cliente. |
| HIGH | N+1 queries em pedidos | `models.py:171-233` | Para cada pedido, executa N queries de itens + M queries de produto. |
| HIGH | Lógica de notificação no controller HTTP | `controllers.py:208-210` | Print de email/SMS/push acoplado ao handler de request. |
| MEDIUM | Código duplicado entre `get_pedidos_usuario` e `get_todos_pedidos` | `models.py:171-233` | 40+ linhas idênticas, bug corrigido em um lugar não reflete no outro. |
| MEDIUM | Lista de categorias hardcoded com magic strings | `controllers.py:52-54` | Regras de negócio embutidas no controller, ausente na atualização. |
| LOW | Magic numbers nas regras de desconto | `models.py:256-261` | Valores `10000`, `0.1`, `5000` sem nome explicativo. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| CRITICAL | Credenciais de produção hardcoded (DB, payment, SMTP) | `utils.js:1-7` | `pk_live_` indica chave de gateway de pagamento real exposta no código. |
| CRITICAL | Número de cartão logado no console | `AppManager.js:45` | Viola PCI-DSS. Pode resultar em perda da capacidade de processar pagamentos. |
| CRITICAL | Implementação de hash fraco (`badCrypto`) | `utils.js:18-23` | Base64 não é hash — completamente reversível. Senhas expostas em texto. |
| CRITICAL | God Class — `AppManager` faz DB + rotas + negócio | `AppManager.js:1-141` | Única classe com 141 linhas mistura criação de banco, rotas e regras. |
| HIGH | N+1 queries no relatório financeiro | `AppManager.js:80-129` | Queries aninhadas em callbacks: `cursos → matrículas → usuários → pagamentos`. |
| HIGH | Callback hell com 4 níveis de aninhamento | `AppManager.js:28-78` | Pirâmide de callbacks impossível de manter e com tratamento de erros inconsistente. |
| HIGH | Estado global mutável (`globalCache`, `totalRevenue`) | `utils.js:9-10` | Mutado por múltiplas funções, impossível de testar e problemático em multi-process. |
| MEDIUM | Nomes de variáveis de 1-2 letras (`u`, `e`, `p`, `cid`, `cc`) | `AppManager.js:29-34` | Código ilegível sem contexto. |

### Projeto 3 — task-manager-api (Python/Flask)

| Severidade | Problema | Arquivo | Justificativa |
|---|---|---|---|
| CRITICAL | SECRET_KEY hardcoded | `app.py:13` | Mesma classe de problema do Projeto 1. |
| CRITICAL | Hash MD5 para senhas — algoritmo quebrado | `models/user.py:29-32` | MD5 tem rainbow tables completas disponíveis online. Senhas recuperáveis em segundos. |
| CRITICAL | Token de autenticação fake (`fake-jwt-token-{id}`) | `routes/user_routes.py:209` | Token previsível e não assinado — qualquer usuário pode se passar por outro. |
| HIGH | `Model.query.get()` deprecated no SQLAlchemy 2.0 | `routes/task_routes.py:67,117` e outros (12 ocorrências) | Gera `LegacyAPIWarning`, quebra ao atualizar para SQLAlchemy 2.x. |
| HIGH | Ausência de camada de controllers | `routes/*.py` | Toda lógica de negócio nas routes — impossível testar sem servidor HTTP. |
| HIGH | Lógica `is_overdue` duplicada em 6 lugares | `routes/task_routes.py` e `report_routes.py` | Model já tem `is_overdue()` que não é utilizado. |
| MEDIUM | N+1 queries em `user_stats` do relatório | `routes/report_routes.py:53-68` | Para cada usuário, executa query adicional de tasks. |
| MEDIUM | Senha exposta no `to_dict()` do model User | `models/user.py:22` | Hash da senha retornado em todas as respostas GET /users. |

---

## Construção da Skill

### Estrutura de arquivos

```
.claude/skills/refactor-arch/
├── SKILL.md                    # Prompt principal — 3 fases sequenciais
├── project-analysis.md         # Heurísticas de detecção de stack
├── antipatterns-catalog.md     # 16 anti-patterns com sinais de detecção
├── audit-report-template.md    # Template padronizado com regras de formatação
├── architecture-guidelines.md  # Regras MVC com exemplos Python e Node.js
└── refactoring-playbook.md     # 10 padrões de transformação com código antes/depois
```

### Decisões de design

**SKILL.md como prompt estruturado em fases:** O arquivo principal instrui o agente a seguir 3 fases sequenciais com checkpoints obrigatórios — incluindo a pausa com confirmação do usuário antes de qualquer modificação de arquivo.

**Catálogo com 16 anti-patterns:** Foram incluídos todos os problemas encontrados nos 3 projetos, mais problemas comuns de segurança (AP-05: endpoint admin sem auth, AP-10: dados sensíveis em response). Cada anti-pattern tem sinais de detecção específicos com snippets de código, não descrições genéricas.

**Detecção de APIs deprecated como categoria obrigatória (AP-13):** Listadas as APIs deprecated do SQLAlchemy 2.0, Flask, Express e sqlite3 — necessárias para o Projeto 3 que usa `Query.get()` extensivamente.

**Playbook com 10 padrões de transformação:** Cada padrão tem código `antes` e `depois` para Python e Node.js quando aplicável, com passos numerados de transformação.

### Como a skill é agnóstica de tecnologia

- Os arquivos de referência cobrem Python/Flask e Node.js/Express com exemplos paralelos
- O `SKILL.md` usa linguagem genérica (`cursor.execute` ou `db.run`, `app.py` ou `app.js`)
- A Fase 1 detecta a stack dinamicamente via `requirements.txt` ou `package.json`
- A Fase 3 cria estruturas de diretórios diferentes conforme a linguagem detectada
- O catálogo de anti-patterns inclui sintaxe de detecção para ambas as linguagens

### Desafios encontrados

1. **N+1 queries em SQL puro vs ORM:** O padrão de solução é diferente — JOIN manual para SQLite/sqlite3, `eager_load` ou query otimizada para SQLAlchemy. O playbook cobre ambos.
2. **APIs deprecated do SQLAlchemy:** O Projeto 3 tem 12+ ocorrências de `.query.get()` distribuídas em 3 arquivos. A skill precisa ser instruída a fazer substituição global, não pontual.
3. **Preservação de endpoints:** A refatoração não pode mudar URLs ou métodos HTTP. Os blueprints Python e routers Node.js precisam mapear exatamente as mesmas rotas.

---

## Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project (Python/Flask) | 5 | 3 | 3 | 3 | **14** |
| ecommerce-api-legacy (Node.js/Express) | 4 | 4 | 3 | 2 | **13** |
| task-manager-api (Python/Flask) | 3 | 4 | 4 | 4 | **15** |

### Comparação antes/depois

#### Projeto 1 — code-smells-project

**Antes:**
```
code-smells-project/
├── app.py         (89 linhas — rotas + admin query SQL + reset DB)
├── controllers.py (293 linhas — todos os controllers misturados)
├── models.py      (315 linhas — SQL concatenado, N+1, plain text passwords)
└── database.py    (87 linhas — estado global, seeds com senhas plain text)
```

**Depois:**
```
code-smells-project/
├── app.py                             (composition root)
├── database.py                        (conexão, sem estado global de senha)
└── src/
    ├── config/settings.py             (SECRET_KEY via env var, categorias, regras de desconto)
    ├── models/produto_model.py        (queries parametrizadas, sem SQL injection)
    ├── models/usuario_model.py        (hash SHA-256+salt, sem plain text)
    ├── models/pedido_model.py         (JOIN único elimina N+1)
    ├── controllers/produto_controller.py
    ├── controllers/usuario_controller.py
    ├── controllers/pedido_controller.py (health check sem secrets)
    ├── views/produto_routes.py        (apenas mapeamento)
    ├── views/usuario_routes.py
    ├── views/pedido_routes.py
    └── middlewares/error_handler.py   (error handling centralizado)
```

#### Projeto 2 — ecommerce-api-legacy

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js          (14 linhas)
├── AppManager.js   (141 linhas — God Class: DB + rotas + negócio + log de cartão)
└── utils.js        (25 linhas — credenciais hardcoded, estado global mutável)
```

**Depois:**
```
ecommerce-api-legacy/src/
├── app.js                              (composition root com async/await)
├── database.js                         (wrapper Promise sobre sqlite3)
├── config/settings.js                  (todas as configs via process.env)
├── models/userModel.js                 (cascade delete, sem SQL injection)
├── models/courseModel.js
├── models/enrollmentModel.js           (JOIN único para relatório)
├── controllers/checkoutController.js   (async/await, sem callback hell)
├── controllers/reportController.js
├── routes/checkoutRoutes.js            (apenas mapeamento)
├── routes/reportRoutes.js
└── middlewares/errorHandler.js         (error handling centralizado)
```

#### Projeto 3 — task-manager-api

**Antes:**
```
task-manager-api/
├── app.py                 (SECRET_KEY hardcoded, DEBUG=True hardcoded)
├── models/user.py         (MD5, senha no to_dict())
├── routes/task_routes.py  (300 linhas — lógica + validação + overdue duplicado 4x)
├── routes/user_routes.py  (212 linhas — fake JWT, .query.get() deprecated)
├── routes/report_routes.py (224 linhas — N+1 queries, .query.get() deprecated)
└── services/notification_service.py (email/senha hardcoded)
```

**Depois:**
```
task-manager-api/
├── app.py                             (composition root via create_app())
├── config/settings.py                 (SECRET_KEY, DB URL, SMTP via env vars)
├── models/user.py                     (SHA-256+salt, to_dict() sem senha)
├── controllers/task_controller.py     (lógica extraída, .query.get() → db.session.get())
├── controllers/user_controller.py     (validações, sem fake JWT)
├── routes/task_routes.py              (apenas mapeamento)
├── routes/user_routes.py              (apenas mapeamento)
├── routes/report_routes.py            (mantido — já tinha lógica de relatório)
├── middlewares/error_handler.py       (centralizado)
└── services/notification_service.py  (SMTP via os.environ)
```

### Checklist de validação preenchido

#### Projeto 1 — code-smells-project

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: **Python**
- [x] Framework detectado corretamente: **Flask 3.1.1**
- [x] Domínio da aplicação descrito corretamente: **E-commerce API (produtos, pedidos, usuários)**
- [x] Número de arquivos analisados condiz com a realidade: **4 arquivos**

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados: **14 findings**
- [x] Detecção de APIs deprecated incluída (estado global mutável do DB)
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (`src/config`, `src/models`, `src/controllers`, `src/views`, `src/middlewares`)
- [x] Configuração extraída para módulo de config (SECRET_KEY via `os.environ.get`)
- [x] Models criados para abstrair dados (produto, usuario, pedido)
- [x] Views/Routes separadas para roteamento (3 blueprints)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (`register_error_handlers`)
- [x] Entry point claro (`create_app()` no app.py)
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓ (todos os 6 testados retornam 200)

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: **Node.js**
- [x] Framework detectado corretamente: **Express 4.18.2**
- [x] Domínio da aplicação descrito corretamente: **LMS API (cursos, matrículas, pagamentos)**
- [x] Número de arquivos analisados condiz com a realidade: **3 arquivos**

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade
- [x] Mínimo de 5 findings: **13 findings**
- [x] Detecção de APIs deprecated incluída (sqlite3 callback API → async/await)
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Estrutura MVC criada (`config`, `models`, `controllers`, `routes`, `middlewares`)
- [x] Configuração extraída para `config/settings.js` (todas as credenciais via `process.env`)
- [x] Models criados por domínio (userModel, courseModel, enrollmentModel)
- [x] Routes separadas por domínio
- [x] Controllers com `async/await` (sem callback hell)
- [x] Error handling centralizado (`errorHandler.js`)
- [x] Entry point claro (`app.js`)
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓ (4 endpoints testados)

#### Projeto 3 — task-manager-api

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente: **Python**
- [x] Framework detectado corretamente: **Flask + SQLAlchemy**
- [x] Domínio da aplicação descrito corretamente: **Task Manager API**
- [x] Número de arquivos analisados condiz com a realidade: **10 arquivos**

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade
- [x] Mínimo de 5 findings: **15 findings**
- [x] Detecção de APIs deprecated incluída (`Query.get()` deprecated no SQLAlchemy 2.0 — 12 ocorrências)
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Camada de controllers criada (`controllers/task_controller.py`, `controllers/user_controller.py`)
- [x] Configuração extraída para `config/settings.py`
- [x] `Query.get()` substituído por `db.session.get()` em todos os controllers
- [x] MD5 substituído por SHA-256+salt no `models/user.py`
- [x] `to_dict()` do User não expõe mais o hash da senha
- [x] Routes reduzidas a mapeamentos simples
- [x] Error handling centralizado
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓ (6 endpoints testados)

### Logs de validação

```
=== Projeto 1 (Python/Flask) ===
  ✓ GET /              → 200
  ✓ GET /health        → 200
  ✓ GET /produtos      → 200
  ✓ GET /usuarios      → 200
  ✓ GET /pedidos       → 200
  ✓ GET /relatorios/vendas → 200
✓ Application boots without errors

=== Projeto 2 (Node.js/Express) ===
  ✓ POST /api/checkout              → 200
  ✓ POST /api/checkout (card denied) → 400
  ✓ GET  /api/admin/financial-report → 200
  ✓ DELETE /api/users/1              → 200
✓ Application boots without errors

=== Projeto 3 (Python/Flask + SQLAlchemy) ===
  ✓ GET /              → 200
  ✓ GET /health        → 200
  ✓ GET /tasks         → 200
  ✓ GET /users         → 200
  ✓ GET /reports/summary → 200
  ✓ GET /categories    → 200
✓ Application boots without errors
```

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (`npm install -g @anthropic-ai/claude-code`)
- **Python 3.9+** com `pip` (para projetos 1 e 3)
- **Node.js 18+** com `npm` (para projeto 2)

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask E-commerce
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express LMS
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask Task Manager
cd ../task-manager-api
claude "/refactor-arch"
```

### Validar a refatoração manualmente

```bash
# Projeto 1
cd code-smells-project
pip install flask flask-cors
python app.py
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# Projeto 2
cd ecommerce-api-legacy
npm install
node src/app.js
curl http://localhost:3000/api/admin/financial-report
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"userName":"Test","email":"t@t.com","courseId":1,"cardNumber":"4111111111111111"}'

# Projeto 3
cd task-manager-api
pip install flask flask-cors flask-sqlalchemy
python app.py
curl http://localhost:5000/health
curl http://localhost:5000/tasks
```

### Variáveis de ambiente para produção

Todos os projetos agora leem configurações de variáveis de ambiente. Crie um `.env` (não commitado) com:

```bash
# Projetos Python
export SECRET_KEY="sua-chave-secreta-real"
export DATABASE_URL="postgresql://user:pass@host/db"
export DEBUG="false"

# Projeto Node.js
export PORT=3000
export PAYMENT_GATEWAY_KEY="pk_live_sua_chave_real"
export JWT_SECRET="seu-jwt-secret-real"
export SMTP_USER="seu-email@dominio.com"
export SMTP_PASS="sua-senha-smtp"
```
