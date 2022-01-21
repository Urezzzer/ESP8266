"""Модуль, предоставляющий api для работы с базой данных"""
import sqlite3


class DataBaseManager:
    """Класс для работы с базой данных"""

    def __init__(self, name):
        self.__conn = sqlite3.connect(name, check_same_thread=False)

        cursor = self.__conn.cursor()

        with open('sql_queries/create_tables.sql', 'r') as queries:
            cursor.executescript(queries.read())
        self.__conn.commit()

    def __del__(self):
        self.__conn.close()

    def overflow(self, count):
        """Метод, проверяющий переполнение"""
        cursor = self.__conn.cursor()
        cursor.execute("""SELECT * FROM temperature""")
        size_temperature = len(cursor.fetchall())
        self.__conn.commit()

        cursor.execute("""SELECT * FROM humidity""")
        size_humidity = len(cursor.fetchall())
        self.__conn.commit()

        return size_temperature > count and size_humidity > count

    def cut(self):
        """Метод, обрезающий таблицы"""
        cursor = self.__conn.cursor()

        cursor.execute("""DELETE FROM humidity WHERE t = (SELECT MIN(t) FROM humidity);""")
        self.__conn.commit()

        cursor.execute("""DELETE FROM temperature WHERE t = (SELECT MIN(t) FROM temperature);""")
        self.__conn.commit()

    def add(self, t, h, dt):
        """Метод внесения данных в БД"""
        cursor = self.__conn.cursor()

        # проверка на переполнение
        if self.overflow(800000):
            self.cut()

        cursor.execute("""SELECT * FROM temperature""")
        size_temperature_before = len(cursor.fetchall())
        self.__conn.commit()

        cursor.execute("""SELECT * FROM humidity""")
        size_humidity_before = len(cursor.fetchall())
        self.__conn.commit()

        cursor.execute("""INSERT or REPLACE INTO temperature (t, value) VALUES (?, ?);""",
                       (dt, t))
        self.__conn.commit()
        cursor.execute("""INSERT or REPLACE INTO humidity (t, value) VALUES (?, ?);""",
                       (dt, h))
        self.__conn.commit()

        cursor.execute("""SELECT * FROM temperature""")
        size_temperature_after = len(cursor.fetchall())
        self.__conn.commit()

        cursor.execute("""SELECT * FROM humidity""")
        size_humidity_after = len(cursor.fetchall())
        self.__conn.commit()

        if (size_humidity_after - size_humidity_before != 1) and \
                (size_temperature_after - size_temperature_before != 1):
            return False

        return True

    def delete(self, dt):
        """"""
        cursor = self.__conn.cursor()
        cursor.execute("""DELETE FROM temperature WHERE t = ?""", (dt, ))
        self.__conn.commit()

        cursor.execute("""DELETE FROM humidity WHERE t = ?""", (dt, ))
        self.__conn.commit()



    def get(self, lower_border=None, upper_border=None, mode='data'):
        """Метод возвращения всех данных из БД"""

        def __data_to_json(rows):
            """Функция, преобразующая данные из внутреннего представления в json"""
            json = {}

            if mode == 'data':
                for i, row in enumerate(rows):
                    json[i] = {
                        't': row[0],
                        'value': row[1]
                    }
            elif mode == 'mean':
                json = {'mean': rows[0][0]}
            return json

        cursor = self.__conn.cursor()

        if mode == 'data':
            select_statement = """SELECT * FROM """
        elif mode == 'mean':
            select_statement = """SELECT ROUND(AVG(value), 1) FROM"""
        else:
            return {
                'success': False
            }

        if lower_border is None and upper_border is None:
            cursor.execute(select_statement + """ temperature""")
            temperature = cursor.fetchall()
            self.__conn.commit()

            cursor.execute(select_statement + """ humidity """)
            humidity = cursor.fetchall()
            self.__conn.commit()
        elif lower_border is None and upper_border is not None:
            cursor.execute(select_statement + """ temperature WHERE t <= ?""", (upper_border,))
            temperature = cursor.fetchall()
            self.__conn.commit()

            cursor.execute(select_statement + """ humidity WHERE t <= ?""", (upper_border,))
            humidity = cursor.fetchall()
            self.__conn.commit()
        elif lower_border is not None and upper_border is None:
            cursor.execute(select_statement + """ temperature WHERE t >= ?""", (lower_border,))
            temperature = cursor.fetchall()
            self.__conn.commit()

            cursor.execute(select_statement + """ humidity WHERE t >= ?""", (lower_border,))
            humidity = cursor.fetchall()
            self.__conn.commit()
        else:
            cursor.execute(select_statement + """ temperature WHERE t >= ? AND t <= ?""", (lower_border, upper_border))
            temperature = cursor.fetchall()
            self.__conn.commit()

            cursor.execute(select_statement + """ humidity WHERE t >= ? AND t <= ?""", (lower_border, upper_border))
            humidity = cursor.fetchall()
            self.__conn.commit()

        return {'temperature': __data_to_json(temperature), 'humidity': __data_to_json(humidity)}
