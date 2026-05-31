/**
 * Controller de Relatórios Financeiros.
 */
const EnrollmentModel = require('../models/enrollmentModel');
const UserModel = require('../models/userModel');

class ReportController {
    constructor(db) {
        this.enrollments = new EnrollmentModel(db);
        this.users = new UserModel(db);
    }

    async financialReport(req, res) {
        const rows = await this.enrollments.getFinancialReport();

        // Agrupa por curso no JavaScript — uma única query ao banco
        const reportMap = {};
        for (const row of rows) {
            if (!reportMap[row.course_id]) {
                reportMap[row.course_id] = {
                    course: row.title,
                    revenue: 0,
                    students: []
                };
            }
            if (row.status === 'PAID' && row.amount) {
                reportMap[row.course_id].revenue += row.amount;
            }
            if (row.student_name) {
                reportMap[row.course_id].students.push({
                    student: row.student_name,
                    paid: row.amount || 0
                });
            }
        }

        return res.status(200).json(Object.values(reportMap));
    }

    async deleteUser(req, res) {
        const id = parseInt(req.params.id);
        if (isNaN(id)) {
            return res.status(400).json({ error: 'ID inválido' });
        }

        const user = await this.users.getById(id);
        if (!user) {
            return res.status(404).json({ error: 'Usuário não encontrado' });
        }

        await this.users.deleteWithCascade(id);
        return res.status(200).json({ message: 'Usuário e dados associados removidos com sucesso' });
    }
}

module.exports = ReportController;
