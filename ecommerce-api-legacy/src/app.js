/**
 * Composition root — monta a aplicação Express usando estrutura MVC.
 *
 * Estrutura MVC criada em src/:
 *   config/settings.js           — configurações via process.env
 *   database.js                  — wrapper Promise sobre sqlite3
 *   models/userModel.js          — queries de usuário (sem SQL injection)
 *   models/courseModel.js        — queries de curso
 *   models/enrollmentModel.js    — matrícula + pagamento + JOIN para relatório
 *   controllers/checkoutController.js — fluxo de checkout (async/await)
 *   controllers/reportController.js   — relatório financeiro
 *   routes/checkoutRoutes.js     — apenas mapeamento URL → controller
 *   routes/reportRoutes.js       — apenas mapeamento URL → controller
 *   middlewares/errorHandler.js  — error handling centralizado
 */
const express = require('express');
const settings = require('./config/settings');
const Database = require('./database');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

const db = new Database(settings.dbPath);

// Inicializa banco e sobe o servidor
db.init().then(() => {
    app.use('/api/checkout', checkoutRoutes(db));
    app.use('/api', reportRoutes(db));

    // Error handler centralizado (deve ser o último middleware)
    app.use(errorHandler);

    app.listen(settings.port, () => {
        console.log(`Frankenstein LMS (refatorado para MVC) rodando na porta ${settings.port}`);
    });
}).catch(err => {
    console.error('Falha ao inicializar banco de dados:', err);
    process.exit(1);
});

module.exports = app;
