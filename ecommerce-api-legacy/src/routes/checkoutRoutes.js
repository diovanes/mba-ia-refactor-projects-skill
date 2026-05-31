/**
 * Rotas de Checkout — apenas mapeamento URL → controller.
 */
const express = require('express');
const CheckoutController = require('../controllers/checkoutController');

module.exports = (db) => {
    const router = express.Router();
    const ctrl = new CheckoutController(db);

    router.post('/', (req, res, next) => ctrl.checkout(req, res).catch(next));

    return router;
};
