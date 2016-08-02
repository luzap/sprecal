import sqlite3


class DbInterface:

    def __init__(self, name):
        self.name = name
        self.conn = sqlite3.connect(self.name)
        self.cursor = self.conn.cursor()
        self.make_table()

    def make_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        desc VARCHAR(200) NOT NULL,
                        date DATE NOT NULL,
                        counter INTEGER NOT NULL DEFAULT(0)
                           )''')

    def make_task(self, data):
        self.cursor.execute("INSERT INTO tasks VALUES(?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (int(task_id),))
        self.conn.commit()

    def get_columns(self):
        self.cursor.execute("PRAGMA table_info(tasks)")
        data = self.cursor.fetchall()
        column = []
        for item in data:
            column.append(item[1])
        return tuple(column)

    def get_rows(self):
        self.cursor.execute("SELECT COUNT(*) FROM tasks")
        return self.cursor.fetchone()

    def get_data(self, date):
        self.cursor.execute("SELECT * FROM tasks WHERE date = ?", (date, ))
        return self.cursor.fetchall()

    def get_last(self):
        self.cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 1")
        return self.cursor.fetchone()[1]

    def change_task(self, task_id, date, counter):
        self.cursor.execute("UPDATE tasks SET date = ? WHERE id = ?", (date, task_id))
        self.cursor.execute("UPDATE tasks SET counter = ? WHERE id = ?", (counter, task_id))
        self.conn.commit()
