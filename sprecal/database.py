# TODO Add comments
# TODO Move all data manipulation here

import sqlite3


class DbInterface:
    """"""
    def __init__(self, filename):
        self._filename = filename
        self._conn = sqlite3.connect(self._filename)
        self._cursor = self._conn.cursor()
        self.__make_table()

    def __make_table(self):
        """"""
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        desc VARCHAR(200) NOT NULL,
                        date DATE NOT NULL,
                        counter INTEGER NOT NULL DEFAULT(0)
                           )''')

    def make_task(self, data):
        """"""
        self._cursor.execute("INSERT INTO tasks VALUES(?, ?, ?, ?, ?)", data)
        self._conn.commit()

    def delete_task(self, task_id):
        """"""
        self._cursor.execute("DELETE FROM tasks WHERE id = ?", (int(task_id),))
        self._conn.commit()

    def search_tasks(self, date):
        raise NotImplementedError

    def get_columns(self):
        """"""
        self._cursor.execute("PRAGMA table_info(tasks)")
        data = self._cursor.fetchall()
        column = [item[1] for item in data]
        return tuple(column)

    def get_rows(self):
        """"""
        self._cursor.execute("SELECT COUNT(*) FROM tasks")
        return self._cursor.fetchone()

    def get_data(self, date):
        """"""
        self._cursor.execute("SELECT * FROM tasks WHERE date = ?", (date,))
        return self._cursor.fetchall()

    def get_last(self):
        """"""
        self._cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 1")
        return self._cursor.fetchone()[1]

    def change_task(self, task_id, date, counter):
        """"""
        self._cursor.execute("UPDATE tasks SET date = ? WHERE id = ?", (date, task_id))
        self._cursor.execute("UPDATE tasks SET counter = ? WHERE id = ?", (counter, task_id))
        self._conn.commit()

    def relearn_old_task(self, date, task_id: int)-> None:
        """If something has not been reviewed on time, set its review count to zero."""
        self._cursor.execute("UPDATE tasks SET date = ?, counter = 0 WHERE id = ?", (date, task_id))
        self._conn.commit()
