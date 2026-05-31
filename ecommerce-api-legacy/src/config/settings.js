/**
 * Configurações centralizadas — lidas de variáveis de ambiente.
 * NUNCA coloque credenciais reais como valores default.
 */
module.exports = {
    port: parseInt(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',

    // Gateway de pagamento — obrigatório em produção
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',

    // SMTP
    smtpUser: process.env.SMTP_USER || '',
    smtpPass: process.env.SMTP_PASS || '',

    // JWT
    jwtSecret: process.env.JWT_SECRET || 'dev-secret-change-in-production',
};
