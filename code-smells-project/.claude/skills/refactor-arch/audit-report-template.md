# Template de Relatório de Auditoria

Use exatamente este formato ao gerar o relatório na Fase 2.

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<total> lines of code
Date:    <data atual>

================================
Summary
================================
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>

================================
Findings
================================

[CRITICAL] <Nome do Anti-Pattern>
File: <caminho/arquivo.py>:<linha-início>-<linha-fim>
Description: <descrição específica do problema encontrado neste arquivo>
Impact: <impacto concreto para esta aplicação>
Recommendation: <ação específica para corrigir>

[CRITICAL] <Nome do Anti-Pattern>
File: <caminho/arquivo.py>:<linha>
Description: <descrição>
Impact: <impacto>
Recommendation: <recomendação>

[HIGH] <Nome do Anti-Pattern>
File: <caminho/arquivo.py>:<linha-início>-<linha-fim>
Description: <descrição específica>
Impact: <impacto>
Recommendation: <recomendação>

[HIGH] <Nome do Anti-Pattern>
...

[MEDIUM] <Nome do Anti-Pattern>
File: <caminho/arquivo.py>:<linha>
Description: <descrição>
Impact: <impacto>
Recommendation: <recomendação>

[LOW] <Nome do Anti-Pattern>
File: <caminho/arquivo.py>:<linha>
Description: <descrição>
Impact: <impacto>
Recommendation: <recomendação>

================================
Total: <N> findings
================================
```

---

## Regras de formatação:

1. **Ordenação obrigatória:** CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada severidade, ordene pelo impacto.

2. **Arquivo e linha:** Sempre inclua o caminho relativo ao diretório do projeto e as linhas exatas. Exemplo: `models.py:28` ou `src/AppManager.js:43-78`.

3. **Descrição específica:** Não descreva o anti-pattern genericamente — descreva o que foi encontrado neste projeto específico. Ruim: "SQL Injection presente". Bom: "Query em `models.py:28` concatena `str(id)` diretamente: `WHERE id = " + str(id)"`".

4. **Recommendation acionável:** Indique exatamente o que fazer. Ruim: "Use queries seguras". Bom: "Substitua a concatenação por parâmetro: `cursor.execute('WHERE id = ?', (id,))`".

5. **APIs deprecated:** Se encontrar uso de APIs deprecated, liste como MEDIUM com referência à versão que as deprecated e o substituto moderno.

6. **Findings mínimos:** O relatório deve ter no mínimo 5 findings. Se o projeto for bem estruturado, ainda assim reporte problemas de qualidade, performance ou APIs deprecated.

---

## Exemplo completo de finding:

```
[CRITICAL] SQL Injection
File: models.py:28
Description: Query concatena ID recebido diretamente como string: `"WHERE id = " + str(id)`. Qualquer valor pode ser injetado no lugar do ID.
Impact: Permite leitura, modificação e exclusão de dados do banco via manipulação do parâmetro de URL.
Recommendation: Substituir por query parametrizada: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`

[CRITICAL] Credenciais Hardcoded
File: app.py:7
Description: SECRET_KEY definida como literal `"minha-chave-super-secreta-123"` no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório tem acesso à chave de sessão, permitindo forjar tokens.
Recommendation: Mover para variável de ambiente: `app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-key")`
```
