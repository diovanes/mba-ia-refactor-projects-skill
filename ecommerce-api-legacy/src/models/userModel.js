/**
 * Model de Usuário — queries parametrizadas, sem SQL injection.
 */
class UserModel {
    constructor(db) {
        this.db = db;
    }

    getById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    getByEmail(email) {
        return this.db.get('SELECT * FROM users WHERE email = ?', [email]);
    }

    async create(name, email, passwordHash) {
        const result = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return result.lastID;
    }

    async deleteWithCascade(id) {
        // Deleta em cascata: payments → enrollments → user
        await this.db.run(
            'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
            [id]
        );
        await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
        const result = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
        return result.changes > 0;
    }
}

module.exports = UserModel;
