# Relatório de Auditoria — Projeto 1

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~700 lines of code
Date:    2026-05-30

================================
Summary
================================
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 3

================================
Findings
================================

[CRITICAL] SQL Injection — Múltiplos Pontos
File: models.py:28
Description: Query concatena ID diretamente como string: `"SELECT * FROM produtos WHERE id = " + str(id)`. Mesma vulnerabilidade em get_usuario_por_id (linha 92), deletar_produto (68), get_pedidos_usuario (174), get_todos_pedidos (220), atualizar_status_pedido (280).
Impact: Qualquer valor pode ser injetado no parâmetro, permitindo leitura ou exclusão arbitrária de dados do banco.
Recommendation: Substituir toda concatenação por queries parametrizadas: `cursor.execute("WHERE id = ?", (id,))`

[CRITICAL] SQL Injection — INSERT com Concatenação de Strings
File: models.py:48-50
Description: INSERT de produto monta a query concatenando `nome`, `descricao` e `categoria` diretamente: `"VALUES ('" + nome + "', '" + descricao + "', ..."`. Mesmo problema em criar_usuario (127-130) e login_usuario (109-111).
Impact: Atacante pode injetar SQL no nome de um produto ou nas credenciais, comprometendo a integridade de todo o banco.
Recommendation: Usar parâmetros posicionais em todas as queries de escrita.

[CRITICAL] Endpoint Administrativo sem Autenticação — SQL Arbitrário
File: app.py:59-78
Description: A rota POST `/admin/query` recebe qualquer string SQL no body e a executa diretamente com `cursor.execute(query)`. Sem nenhuma verificação de autenticação.
Impact: Qualquer usuário pode destruir dados, ler senhas ou executar DROP TABLE via requisição HTTP.
Recommendation: Remover este endpoint completamente ou proteger com autenticação de admin robusta.

[CRITICAL] Credenciais Hardcoded
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — chave de sessão com valor literal no código-fonte.
Impact: Exposição do repositório vaza a chave, permitindo forjar tokens de sessão.
Recommendation: Mover para variável de ambiente: `os.environ.get('SECRET_KEY', 'dev-key')`

[CRITICAL] Senhas em Plain Text
File: database.py:76-82 e models.py:122-131
Description: Senhas de usuários inseridas e armazenadas como texto puro. Seed inclui `("Admin", "admin@loja.com", "admin123", "admin")`. Login compara a string diretamente (`WHERE senha = ?`).
Impact: Vazamento do banco expõe todas as senhas dos usuários diretamente. Viola LGPD.
Recommendation: Usar `hashlib` com salt ou `bcrypt` para hash das senhas antes de armazenar.

[HIGH] Informações Sensíveis Expostas na API
File: controllers.py:284-292
Description: O endpoint `/health` retorna `"secret_key": "minha-chave-super-secreta-123"`, `"debug": True` e `"db_path": "loja.db"` na resposta JSON.
Impact: Qualquer cliente pode chamar `/health` e obter a chave secreta da aplicação e detalhes de infraestrutura.
Recommendation: Remover todos os campos de configuração interna. Retornar apenas `{"status": "ok", "version": "1.0.0"}`.

[HIGH] N+1 Queries — Pedidos com Itens e Produtos
File: models.py:171-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam 1 query para pedidos + N queries para itens + N×M queries para nomes de produtos. Com 10 pedidos de 3 itens cada = 31+ queries por chamada.
Impact: Performance degradada exponencialmente com o crescimento de dados.
Recommendation: Substituir por JOIN único: `SELECT p.*, ip.*, pr.nome FROM pedidos p LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id LEFT JOIN produtos pr ON pr.id = ip.produto_id`.

[HIGH] Lógica de Negócio de Notificação no Controller HTTP
File: controllers.py:208-210 e 248-251
Description: O controller `criar_pedido` contém prints simulando envio de email, SMS e push. O controller `atualizar_status_pedido` contém lógica condicional de notificação diretamente no handler HTTP.
Impact: Lógica de negócio presa no controller, impossível de reutilizar ou testar isoladamente.
Recommendation: Extrair para um `NotificationService` separado.

[MEDIUM] Código Duplicado — get_pedidos_usuario e get_todos_pedidos
File: models.py:171-233
Description: As funções `get_pedidos_usuario` e `get_todos_pedidos` têm estrutura idêntica (loop com N+1), diferindo apenas por um filtro `WHERE usuario_id`. Aproximadamente 40 linhas duplicadas.
Impact: Bug na lógica de serialização de itens precisa ser corrigido em dois lugares.
Recommendation: Criar uma função privada `_get_pedidos(db, usuario_id=None)` que ambas chamam.

[MEDIUM] Validação de Categoria com Magic Strings no Controller
File: controllers.py:52-54
Description: Lista de categorias válidas `["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` hardcoded no controller. Ausente na função de atualização.
Impact: Inconsistência entre criação e atualização de produto. Mudança de regra requer atualizar múltiplos lugares.
Recommendation: Extrair para constante em `config/settings.py` ou usar um Enum.

[MEDIUM] Estado Global Mutável — Conexão de Banco
File: database.py:4-5
Description: `db_connection = None` é uma variável global mutável, compartilhada entre todas as requests. `check_same_thread=False` desabilita proteção do SQLite.
Impact: Em ambiente multi-thread (produção com gunicorn), pode causar race conditions e corrupção de dados.
Recommendation: Usar `flask.g` para conexão por request ou um connection pool via SQLAlchemy.

[LOW] Magic Numbers nas Regras de Desconto
File: models.py:256-261
Description: Valores `10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02` hardcoded sem nomes explicativos nas regras de desconto de `relatorio_vendas`.
Impact: Difícil entender o significado dos thresholds. Mudança de regra requer caçar todos os números.
Recommendation: Extrair como constantes nomeadas: `DESCONTO_OURO = 0.1`, `LIMITE_OURO = 10000`.

[LOW] Logging com print() em vez de logger
File: controllers.py:8, 57, 107, 179 e outros
Description: Uso de `print()` para logging em toda a aplicação (cerca de 15 ocorrências).
Impact: Sem controle de nível (DEBUG/INFO/ERROR), sem timestamps automáticos, não funciona em ambientes de produção.
Recommendation: Substituir por `import logging; logger = logging.getLogger(__name__)`.

[LOW] Rota de Reset de Banco sem Proteção
File: app.py:47-57
Description: Rota POST `/admin/reset-db` deleta todos os dados de todas as tabelas sem autenticação.
Impact: Qualquer usuário pode esvaziar o banco de produção com uma única requisição HTTP.
Recommendation: Remover ou proteger com autenticação de administrador e token CSRF.

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n] > y
```
