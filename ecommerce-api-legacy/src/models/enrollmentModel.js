/**
 * Model de Matrícula e Pagamento.
 */
class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create(userId, courseId) {
        const result = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return result.lastID;
    }

    async createPayment(enrollmentId, amount, status) {
        const result = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return result.lastID;
    }

    async logAudit(action) {
        await this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
    }

    /**
     * Relatório financeiro com JOIN único — elimina N+1 queries.
     */
    getFinancialReport() {
        return this.db.all(`
            SELECT c.id AS course_id,
                   c.title,
                   u.name AS student_name,
                   pay.amount,
                   pay.status
            FROM courses c
            LEFT JOIN enrollments e  ON e.course_id = c.id
            LEFT JOIN users u        ON u.id = e.user_id
            LEFT JOIN payments pay   ON pay.enrollment_id = e.id
            WHERE c.active = 1
            ORDER BY c.id
        `);
    }
}

module.exports = EnrollmentModel;
