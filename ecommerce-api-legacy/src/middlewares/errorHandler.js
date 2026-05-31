/**
 * Error handler centralizado para Express.
 * Captura erros lançados por controllers async.
 */
function errorHandler(err, req, res, next) {
    console.error('[ERROR]', err.message);

    const status = err.status || 500;
    const message = process.env.NODE_ENV === 'production'
        ? 'Internal Server Error'
        : err.message;

    res.status(status).json({ error: message });
}

module.exports = errorHandler;
