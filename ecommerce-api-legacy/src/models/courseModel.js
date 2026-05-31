/**
 * Model de Curso.
 */
class CourseModel {
    constructor(db) {
        this.db = db;
    }

    getById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }

    getAll() {
        return this.db.all('SELECT * FROM courses WHERE active = 1');
    }
}

module.exports = CourseModel;
