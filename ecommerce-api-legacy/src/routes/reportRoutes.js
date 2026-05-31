/**
 * Rotas de Relatórios e Administração.
 */
const express = require('express');
const ReportController = require('../controllers/reportController');

module.exports = (db) => {
    const router = express.Router();
    const ctrl = new ReportController(db);

    router.get('/admin/financial-report', (req, res, next) => ctrl.financialReport(req, res).catch(next));
    router.delete('/users/:id', (req, res, next) => ctrl.deleteUser(req, res).catch(next));

    return router;
};
