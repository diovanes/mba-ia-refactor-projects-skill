# Relatório de Auditoria — Projeto 3

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (SQLAlchemy ORM)
Files:   10 analyzed (app.py, database.py, seed.py, models/*, routes/*, services/*, utils/*) | ~600 lines de código
Date:    2026-05-30
Note:    Projeto parcialmente organizado — possui models/, routes/, services/, utils/ mas sem camada de controllers

================================
Summary
================================
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 4

================================
Findings
================================

[CRITICAL] SECRET_KEY Hardcoded
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` — chave de sessão com valor literal no código-fonte.
Impact: Qualquer acesso ao repositório revela a chave. Permite forjar tokens de sessão.
Recommendation: Substituir por `os.environ.get('SECRET_KEY', 'dev-key-change-in-production')`.

[CRITICAL] Hash de Senha com MD5 — Algoritmo Criptograficamente Quebrado
File: models/user.py:29-32
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()`. MD5 foi quebrado criptograficamente em 2004. Existem rainbow tables completas para MD5. `check_password` também compara MD5 diretamente.
Impact: Qualquer banco de dados vazado expõe todas as senhas em segundos usando ferramentas como hashcat ou online rainbow tables.
Recommendation: Substituir por `hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000)` ou instalar bcrypt: `bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())`.

[CRITICAL] Token de Autenticação Falso (Fake JWT)
File: routes/user_routes.py:209
Description: O endpoint `/login` retorna `'token': 'fake-jwt-token-' + str(user.id)` — um token previsível e não assinado. Qualquer cliente pode forjar o token de qualquer usuário conhecendo apenas o ID.
Impact: Ausência total de autenticação real. Qualquer pessoa pode acessar rotas protegidas se souber o ID de um usuário.
Recommendation: Implementar JWT real usando `pip install PyJWT` e assinar o token com SECRET_KEY.

[HIGH] API Deprecated — SQLAlchemy 2.0: Query.get()
File: routes/task_routes.py:67, 117, 159, 190, 229 e routes/user_routes.py:29, 94, 136, 155 e routes/report_routes.py:105, 193, 211
Description: Uso extensivo de `Model.query.get(id)` — método deprecated desde SQLAlchemy 1.4 e removido no 2.0. Gera `LegacyAPIWarning` e quebrará ao atualizar para SQLAlchemy 2.x.
Impact: 12+ ocorrências distribuídas nos 3 arquivos de rotas. Migração para SQLAlchemy 2.x quebra a aplicação completamente.
Recommendation: Substituir TODOS por `db.session.get(Model, id)`. Exemplo: `Task.query.get(task_id)` → `db.session.get(Task, task_id)`.

[HIGH] Lógica de Negócio nas Routes (Ausência de Controllers)
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-224
Description: Os 3 arquivos de routes contêm toda a lógica de negócio diretamente nas funções de rota: validações complexas, cálculos de overdue, geração de relatórios. Não existe camada de controllers entre routes e models.
Impact: Routes com 50-100 linhas de lógica. Impossível testar a lógica de negócio sem subir o servidor HTTP.
Recommendation: Criar pasta `controllers/` e mover a lógica de negócio para controladores dedicados por domínio.

[HIGH] Cálculo de Overdue Duplicado em 5+ Lugares
File: routes/task_routes.py:31-39, 71-80, 172-178, 283-287; routes/report_routes.py:33-43, 133-135
Description: O bloco `if t.due_date: if t.due_date < datetime.utcnow(): if t.status not in ['done', 'cancelled']:` aparece pelo menos 6 vezes no código, praticamente idêntico. O model `Task` já tem o método `is_overdue()` que não está sendo usado.
Impact: Bug de regra de overdue precisa ser corrigido em 6 lugares. Inconsistência é altamente provável.
Recommendation: Usar o método `task.is_overdue()` que já existe em `models/task.py:50`. Remover os 6 blocos duplicados.

[HIGH] Credenciais SMTP Hardcoded no Serviço
File: services/notification_service.py:9-10
Description: `self.email_password = 'senha123'` e `self.email_user = 'taskmanager@gmail.com'` hardcoded no construtor da classe `NotificationService`.
Impact: Exposição de credenciais de email da aplicação. Em produção, permite envio de emails em nome da aplicação.
Recommendation: Ler de variáveis de ambiente: `os.environ.get('SMTP_USER', '')` e `os.environ.get('SMTP_PASS', '')`.

[MEDIUM] N+1 Queries em report_routes.py — user_stats
File: routes/report_routes.py:53-68
Description: Para gerar `user_stats`, itera sobre todos os usuários e para cada um executa `Task.query.filter_by(user_id=u.id).all()` — uma query por usuário.
Impact: Com 100 usuários = 101 queries ao banco. Performance degrada linearmente.
Recommendation: Usar `db.session.query(User, db.func.count(Task.id)).outerjoin(Task).group_by(User.id).all()` para buscar tudo em uma query.

[MEDIUM] Senha Exposta no to_dict() do Model User
File: models/user.py:16-25
Description: O método `to_dict()` inclui `'password': self.password` — o hash da senha é retornado em todas as respostas de API que serializam usuários.
Impact: Hash MD5 da senha exposto em todas as chamadas GET /users, GET /users/:id, GET /login. Facilita ataques de rainbow table.
Recommendation: Remover o campo `password` do `to_dict()`. Nunca serializar senhas, mesmo hasheadas.

[MEDIUM] Imports Não Utilizados nas Routes
File: routes/task_routes.py:7
Description: `import json, os, sys, time` — nenhum desses módulos é usado no arquivo `task_routes.py`.
Impact: Poluição de namespace. Pode mascarar erros reais de import. Viola o princípio de importar apenas o necessário.
Recommendation: Remover todos os imports não utilizados.

[MEDIUM] Ausência de Error Handling Centralizado
File: routes/task_routes.py, routes/user_routes.py, routes/report_routes.py
Description: Mistura de `try/except Exception` genérico, `except:` sem tipo, e funções sem nenhum tratamento de erro. Formato de resposta de erro inconsistente entre rotas.
Impact: Erros inesperados podem resultar em respostas 500 com stack traces, ou em respostas sem corpo se o except estiver vazio.
Recommendation: Criar `middlewares/error_handler.py` com `register_error_handlers(app)` para Flask.

[LOW] Bare except em Múltiplos Lugares
File: routes/task_routes.py:62, 138, 152, 235; routes/report_routes.py:187, 208, 220
Description: Uso de `except:` sem especificar o tipo de exceção — captura inclusive `SystemExit`, `KeyboardInterrupt` e `GeneratorExit`.
Impact: Oculta erros inesperados. Pode impedir o programa de terminar corretamente.
Recommendation: Substituir `except:` por `except Exception as e:` com logging adequado.

[LOW] isinstance() vs type() para Verificação de Tipo
File: routes/task_routes.py:141
Description: `if type(tags) == list:` — comparação direta de tipo em vez de `isinstance(tags, list)`.
Impact: Não funciona corretamente com subclasses de list. Antipadrão Python.
Recommendation: Substituir por `if isinstance(tags, list):`.

[LOW] Logging com print() em vez de logger
File: routes/task_routes.py:149, 219, 232; routes/user_routes.py:83, 88, 147
Description: Uso de `print(f"Task criada: ...")` e `print(f"ERRO: ...")` para logging em múltiplos lugares.
Impact: Sem nível de log, sem timestamps automáticos, não configurável para produção.
Recommendation: Substituir por `import logging; logger = logging.getLogger(__name__)`.

[LOW] DEBUG=True no Entry Point
File: app.py:34
Description: `app.run(debug=True, ...)` hardcoded. Modo debug em produção expõe o Werkzeug debugger interativo — permite execução de código Python arbitrário.
Impact: Vulnerabilidade crítica de segurança se o app for deployed em produção com este setting.
Recommendation: Ler de variável de ambiente: `debug=os.environ.get('DEBUG', 'False').lower() == 'true'`.

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n] > y
```
