/**
 * Controller de Checkout — orquestra o fluxo de matrícula.
 * Sem callbacks aninhados, sem credenciais hardcoded, sem log de cartão.
 */
const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const EnrollmentModel = require('../models/enrollmentModel');

class CheckoutController {
    constructor(db) {
        this.users = new UserModel(db);
        this.courses = new CourseModel(db);
        this.enrollments = new EnrollmentModel(db);
    }

    async checkout(req, res) {
        const { userName, email, password, courseId, cardNumber } = req.body;

        if (!userName || !email || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Campos obrigatórios: userName, email, courseId, cardNumber' });
        }

        const course = await this.courses.getById(courseId);
        if (!course) {
            return res.status(404).json({ error: 'Curso não encontrado ou inativo' });
        }

        // Simula processamento do cartão (NUNCA logar número real do cartão)
        const paymentStatus = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
        if (paymentStatus === 'DENIED') {
            return res.status(400).json({ error: 'Pagamento recusado' });
        }

        // Busca ou cria usuário
        let user = await this.users.getByEmail(email);
        if (!user) {
            // Em produção: usar bcrypt.hash(password, 10)
            const passwordHash = Buffer.from(password || 'default').toString('base64');
            const newUserId = await this.users.create(userName, email, passwordHash);
            user = { id: newUserId };
        }

        // Cria matrícula e pagamento
        const enrollmentId = await this.enrollments.create(user.id, courseId);
        await this.enrollments.createPayment(enrollmentId, course.price, paymentStatus);
        await this.enrollments.logAudit(`Checkout: curso ${courseId} por user ${user.id}`);

        return res.status(200).json({
            message: 'Matrícula realizada com sucesso',
            enrollmentId,
            course: course.title,
            amount: course.price
        });
    }
}

module.exports = CheckoutController;
