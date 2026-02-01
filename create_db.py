import pymysql
from config import host, user, password


def create_database():
    """Создание базы данных и всех необходимых таблиц"""
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()

        # Создаем базу данных

        cursor.execute("CREATE DATABASE IF NOT EXISTS `nail-salon`")

        conn.select_db('nail-salon')

        # Таблица мастеров
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER AUTO_INCREMENT PRIMARY KEY,
            surname TEXT NOT NULL,
            name TEXT NOT NULL,
            patronymic TEXT NOT NULL
        );
        """)

        # Таблица клиентов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER AUTO_INCREMENT PRIMARY KEY,
            surname TEXT COMMENT 'Фамилия',
            name TEXT NOT NULL COMMENT 'Имя', 
            patronymic TEXT COMMENT 'Отчество',
            phone VARCHAR(12) NOT NULL UNIQUE,
            CONSTRAINT chk_phone_format CHECK (phone REGEXP '^\\\\+[0-9]{11}$')
        );
        """)

        # Таблица услуг
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER AUTO_INCREMENT PRIMARY KEY,
            name TEXT COMMENT 'Наименование',
            duration INTEGER NOT NULL CHECK (duration > 0) COMMENT 'Длительность в минутах',
            cost INTEGER NOT NULL CHECK (cost > 0) COMMENT 'Стоимость'
        );
        """)

        # Таблица расписания мастеров по дням недели
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_schedule (
            id INT AUTO_INCREMENT PRIMARY KEY,
            master_id INT NOT NULL,
            day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 1=Пн, 7=Вс
            work_date DATE NOT NULL, -- Конкретная дата
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            FOREIGN KEY (master_id) REFERENCES masters(id) ON DELETE CASCADE,
            UNIQUE KEY unique_master_day (master_id, work_date, start_time)
        );
        """)



        # Таблица записей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT NOT NULL,
            master_id INT NOT NULL,
            service_id INT NOT NULL,
            appointment_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            total_price DECIMAL(10,2) NOT NULL DEFAULT 0,
            status ENUM('Выполнено', 'Отменено', 'Ожидается', 'В процессе') DEFAULT 'Ожидается',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (master_id) REFERENCES masters(id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
        );
        """)


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                master_id INT NOT NULL,
                service_id INT NOT NULL,
                FOREIGN KEY (master_id) REFERENCES masters(id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                UNIQUE KEY unique_master_service (master_id, service_id)
        );
        """)

        conn.commit()
        print("База данных и таблицы успешно созданы!")
        return True

    except Exception as ex:
        print(f"Ошибка при создании БД: {ex}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    create_database()