# Análise de Projeto — Heurísticas de Detecção

## 1. Detecção de Linguagem

### Python
- Arquivo `requirements.txt` ou `pyproject.toml` ou `setup.py` presente
- Extensão `.py` nos arquivos de código
- `if __name__ == '__main__':` no entry point
- Pastas `__pycache__/` ou arquivos `.pyc`

### Node.js / JavaScript
- Arquivo `package.json` presente
- Extensão `.js`, `.ts`, `.mjs` nos arquivos de código
- Pasta `node_modules/` (se instaladas as dependências)
- `"main"` ou `"scripts"` no `package.json`

### Ruby
- `Gemfile` ou `Gemfile.lock` presente
- Extensão `.rb`
- `config.ru` (Rack app)

### Java
- `pom.xml` (Maven) ou `build.gradle` (Gradle) presente
- Extensão `.java`
- Estrutura `src/main/java/`

---

## 2. Detecção de Framework

### Python
| Framework | Indicadores |
|-----------|-------------|
| Flask | `flask` em requirements.txt; `from flask import Flask`; `app = Flask(__name__)` |
| Django | `django` em requirements.txt; `settings.py` com `INSTALLED_APPS`; `manage.py` |
| FastAPI | `fastapi` em requirements.txt; `from fastapi import FastAPI`; `@app.get()` |

### Node.js
| Framework | Indicadores |
|-----------|-------------|
| Express | `express` em package.json; `require('express')`; `app.get()`, `app.post()` |
| Fastify | `fastify` em package.json; `require('fastify')()` |
| NestJS | `@nestjs/core` em package.json; decorators `@Controller()`, `@Module()` |
| Koa | `koa` em package.json; `new Koa()` |

---

## 3. Detecção de Banco de Dados

### SQLite
- Arquivo `.db` ou `.sqlite` no projeto
- `sqlite3` em requirements/package.json
- URI `sqlite:///` no código
- `new sqlite3.Database(':memory:')` ou similar

### PostgreSQL
- `psycopg2` ou `pg` em dependências
- URI `postgresql://` ou `postgres://`
- `DATABASE_URL` com prefixo postgres

### MySQL
- `pymysql`, `mysqlclient`, ou `mysql2` em dependências
- URI `mysql://`

### SQLAlchemy (Python ORM)
- `sqlalchemy` ou `flask-sqlalchemy` em requirements.txt
- `db = SQLAlchemy()` ou `from flask_sqlalchemy import SQLAlchemy`
- Models com `db.Model` como base

### Prisma / Sequelize / TypeORM (Node.js ORMs)
- `prisma`, `sequelize`, ou `typeorm` em package.json
- `schema.prisma` para Prisma

---

## 4. Mapeamento de Arquitetura Atual

### Padrões a identificar:

#### Monolítico (tudo em poucos arquivos)
- Menos de 5 arquivos de código
- Um único arquivo contém rotas, lógica de negócio e acesso a dados
- Sinal: arquivo > 200 linhas misturando responsabilidades

#### Parcialmente organizado
- Pastas `models/`, `routes/`, `controllers/` existem mas não são completas
- Lógica de negócio vazando para as routes
- Sem camada de controllers definida

#### Bem estruturado (mas com problemas)
- MVC claramente separado
- Problemas são de segurança, performance, ou qualidade de código
- Anti-patterns específicos em módulos isolados

---

## 5. Mapeamento de Domínios

Para cada arquivo de código, identifique qual domínio ele representa:

- **Usuários/Auth:** `user`, `usuario`, `auth`, `login`, `session`
- **Produtos:** `product`, `produto`, `item`, `catalog`
- **Pedidos:** `order`, `pedido`, `checkout`, `cart`
- **Tarefas:** `task`, `todo`, `tarefa`
- **Cursos/LMS:** `course`, `enrollment`, `payment`, `lesson`
- **Relatórios:** `report`, `relatorio`, `analytics`, `stats`

---

## 6. Estimativa de Linhas de Código

```bash
# Python
find . -name "*.py" -not -path "./.git/*" | xargs wc -l

# Node.js
find . -name "*.js" -not -path "./node_modules/*" -not -path "./.git/*" | xargs wc -l
```

---

## 7. Checklist de Análise

Ao final da Fase 1, confirme que você identificou:

- [ ] Linguagem e versão (se disponível)
- [ ] Framework e versão
- [ ] Banco de dados
- [ ] Domínio principal da aplicação
- [ ] Lista de todos os arquivos de código
- [ ] Contagem de linhas
- [ ] Tabelas do banco ou models
- [ ] Estilo de arquitetura atual
