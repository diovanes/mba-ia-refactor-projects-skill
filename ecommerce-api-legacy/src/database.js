/**
 * Módulo de banco de dados — inicialização e seed.
 * Usa a API de callback do sqlite3 encapsulada em Promises para async/await.
 */
const sqlite3 = require('sqlite3').verbose();

class Database {
    constructor(path) {
        this.db = new sqlite3.Database(path);
    }

    /** Wrapper Promise para db.run */
    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function (err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    /** Wrapper Promise para db.get (retorna uma linha) */
    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => {
                if (err) reject(err);
                else resolve(row);
            });
        });
    }

    /** Wrapper Promise para db.all (retorna todas as linhas) */
    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => {
                if (err) reject(err);
                else resolve(rows || []);
            });
        });
    }

    /** Cria schema e insere dados de seed */
    async init() {
        await this.run("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
        await this.run("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
        await this.run("CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
        await this.run("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
        await this.run("CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");

        // Seed — senha hasheada (bcrypt recomendado em produção)
        await this.run("INSERT OR IGNORE INTO users (id, name, email, pass) VALUES (1, 'Leonan', 'leonan@fullcycle.com.br', '$seed_hash$')");
        await this.run("INSERT OR IGNORE INTO courses (id, title, price, active) VALUES (1, 'Clean Architecture', 997.00, 1)");
        await this.run("INSERT OR IGNORE INTO courses (id, title, price, active) VALUES (2, 'Docker', 497.00, 1)");
        await this.run("INSERT OR IGNORE INTO enrollments (id, user_id, course_id) VALUES (1, 1, 1)");
        await this.run("INSERT OR IGNORE INTO payments (id, enrollment_id, amount, status) VALUES (1, 1, 997.00, 'PAID')");
    }
}

module.exports = Database;
