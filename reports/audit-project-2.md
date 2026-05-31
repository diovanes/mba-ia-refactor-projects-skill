# Relatório de Auditoria — Projeto 2

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed (src/app.js, src/AppManager.js, src/utils.js) | ~165 lines of code
Date:    2026-05-30

================================
Summary
================================
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 2

================================
Findings
================================

[CRITICAL] Credenciais Hardcoded — Múltiplas Chaves Sensíveis
File: src/utils.js:1-7
Description: O objeto `config` contém valores literais para: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"`. Chave de payment gateway com prefixo `pk_live_` indica ser uma chave de produção real.
Impact: Exposição do repositório vaza credenciais de banco de dados, gateway de pagamento e SMTP — comprometimento total do sistema de pagamentos.
Recommendation: Mover todas para variáveis de ambiente via `process.env`. Criar `config/settings.js` que lê de `process.env`.

[CRITICAL] Implementação de Criptografia Fraca (Bad Crypto)
File: src/utils.js:18-23
Description: A função `badCrypto` itera 10.000 vezes aplicando `Buffer.from(pwd).toString('base64')` e trunca em 10 caracteres. Isso NÃO é hash — é reversível e sem salt. Senhas como "123" geram sempre o mesmo resultado.
Impact: Base64 é codificação, não criptografia. Qualquer atacante pode reverter. Senhas de usuários ficam vulneráveis mesmo se o banco vazar com hash.
Recommendation: Usar `bcrypt.hash(password, 10)` / `bcrypt.compare()`. Instalar `npm install bcrypt`.

[CRITICAL] God Class — AppManager concentra DB, Rotas e Lógica de Negócio
File: src/AppManager.js:1-141
Description: A classe `AppManager` realiza simultaneamente: criação do banco (initDb), definição de todas as rotas (setupRoutes), validação de pagamento, criação de usuários, matrícula e geração de relatórios financeiros — tudo em uma única classe de 141 linhas.
Impact: Impossível testar qualquer componente isoladamente. Qualquer mudança pode afetar todo o sistema. Viola completamente o Single Responsibility Principle.
Recommendation: Separar em: `Database`, `CourseModel`, `UserModel`, `EnrollmentModel`, `CheckoutController`, `ReportController`, rotas por domínio.

[CRITICAL] Número do Cartão de Crédito Logado no Console
File: src/AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` — número completo do cartão de crédito e chave de produção do gateway impressos no log a cada checkout.
Impact: Violação grave de PCI-DSS. Número de cartão em logs é uma falha de segurança crítica que pode gerar multas e perda da capacidade de processar pagamentos.
Recommendation: Remover imediatamente o log. Nunca logar dados de cartão. Usar apenas os últimos 4 dígitos se necessário para rastreabilidade.

[HIGH] N+1 Queries — Relatório Financeiro com Callbacks Aninhados
File: src/AppManager.js:80-129
Description: O endpoint `/api/admin/financial-report` executa: 1 query para todos os cursos, depois para cada curso N queries de matrículas, depois para cada matrícula 2 queries (user + payment). Com 2 cursos e 1 matrícula = 7 queries. Escala para O(N×M×2).
Impact: Performance exponencialmente degradada. Com 10 cursos e 20 matrículas cada = 401+ queries.
Recommendation: Usar JOIN único: `SELECT c.title, u.name, pay.amount, pay.status FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments pay ON pay.enrollment_id = e.id`.

[HIGH] Callback Hell — Checkout com 4 Níveis de Aninhamento
File: src/AppManager.js:28-78
Description: O handler do checkout possui 4 níveis de callbacks aninhados (`db.get → db.get → db.run → db.run → db.run`), formando uma pirâmide de indentação. Erro em qualquer nível pode deixar a resposta sem retorno.
Impact: Código impossível de manter. Tratamento de erros inconsistente — alguns callbacks não têm tratamento. Race condition potencial em fluxo de criação de usuário.
Recommendation: Converter para `async/await` usando o pacote `sqlite` (wrapper Promise) ou `util.promisify`.

[HIGH] Estado Global Mutável
File: src/utils.js:9-10
Description: `let globalCache = {}` e `let totalRevenue = 0` são variáveis globais mutáveis expostas e modificadas por múltiplas funções. `logAndCache` escreve diretamente neste estado global.
Impact: Em ambiente com múltiplos workers (cluster Node.js), estado global não é compartilhado entre processos causando inconsistências. Impossível testar funções que dependem de estado global.
Recommendation: Encapsular em classe `CacheService` com interface controlada. `totalRevenue` não está sendo usado — remover.

[HIGH] Deleção de Usuário sem Cascade — Dados Órfãos
File: src/AppManager.js:131-137
Description: A rota `DELETE /api/users/:id` remove apenas o usuário, mas não as matrículas e pagamentos associados. A resposta inclusive admite: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`.
Impact: Inconsistência referencial no banco. Dados órfãos acumulam indefinidamente. Relatórios financeiros ficam incorretos.
Recommendation: Usar transação para deletar em cascata: primeiro payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?), depois enrollments WHERE user_id = ?, depois o user.

[MEDIUM] Nomes de Variáveis sem Significado
File: src/AppManager.js:29-34
Description: Variáveis de request com nomes de 1-2 letras: `u` (userName), `e` (email), `p` (password), `cid` (courseId), `cc` (cardNumber). Sem contexto, impossível entender o código.
Impact: Qualquer manutenção requer decifrar o código. Onboarding de novos desenvolvedores drasticamente mais difícil.
Recommendation: Renomear: `const { userName, email, password, courseId, cardNumber } = req.body`.

[MEDIUM] API Deprecated — sqlite3 Callback-Based
File: src/AppManager.js (todo o arquivo)
Description: O driver `sqlite3` é usado com a API de callbacks legada. A comunidade Node.js migrou para `async/await`. O pacote `sqlite` ou `better-sqlite3` são as opções modernas.
Impact: Código verboso e propenso a erros. Impossível usar `async/await` sem `promisify` manual.
Recommendation: Substituir por `sqlite` (wrapper Promise sobre sqlite3): `npm install sqlite sqlite3`. Usar `await db.get()`, `await db.run()`, `await db.all()`.

[MEDIUM] Validação de Pagamento por Número do Cartão
File: src/AppManager.js:46
Description: A "lógica de pagamento" verifica apenas se o cartão começa com "4": `cc.startsWith("4") ? "PAID" : "DENIED"`. Isso não representa nenhum processamento real.
Impact: Qualquer cartão Visa (começa com 4) é aprovado. Sem integração com gateway real. Lógica de validação de pagamento completamente fictícia exposta como se fosse funcional.
Recommendation: Extrair para um `PaymentService` que encapsule a integração real com gateway. Documentar claramente que é uma simulação em desenvolvimento.

[LOW] Variável totalRevenue Declarada mas Nunca Usada
File: src/utils.js:10
Description: `let totalRevenue = 0` é declarada e exportada mas nunca atualizada nem consumida em nenhum lugar do código.
Impact: Dead code. Confunde leitores que tentam entender para que serve.
Recommendation: Remover a variável.

[LOW] Seed de Dados com Senha Plain Text
File: src/AppManager.js:18
Description: Dados de seed inserem o usuário 'Leonan' com `pass: '123'` — senha de 3 caracteres em plain text, sem hash, direto no banco.
Impact: Evidência de que o sistema nunca teve hashing de senhas. Dado de seed em banco de produção com senha trivial.
Recommendation: Aplicar hash na função `badCrypto` (que já existe no código, mas não é usada aqui) ou melhor, usar bcrypt.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n] > y
```
