import pymysql
from datetime import datetime, timedelta, date
from config import *
from timedelta_work import timedelta_to_string


def get_connection(): #возвращает объект подключение к бд
    """Создание соединения с базой данных"""
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )


# ========== МАСТЕРА ==========
def get_masters():
    #Получение списка всех мастеров
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM masters ORDER BY surname, name")
            return cursor.fetchall()


def add_master(surname, name, patronymic):
    #Добавление нового мастера
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO masters (surname, name, patronymic) VALUES (%s, %s, %s)",
                (surname, name, patronymic)
            )
            conn.commit()
            return cursor.lastrowid


def update_master(master_id, surname, name, patronymic):
    #Обновление информации о мастере
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE masters SET surname=%s, name=%s, patronymic=%s WHERE id=%s",
                (surname, name, patronymic, master_id)
            )
            conn.commit()
            return cursor.rowcount


def delete_master(master_id):
    #Удаление мастера
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM masters WHERE id=%s", (master_id,))
            conn.commit()
            return cursor.rowcount


# ========== КЛИЕНТЫ ==========
def get_clients():
    #Получение списка всех клиентов
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, CONCAT(COALESCE(surname, ''), ' ', name, ' ', COALESCE(patronymic, '')) as full_name, phone 
                FROM clients 
                ORDER BY surname, name;
            """)
            return cursor.fetchall()


def get_client_by_id(client_id):
    #Получение клиента по ID
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM clients WHERE id=%s", (client_id,))
            return cursor.fetchone()


def add_client(surname, name, patronymic, phone):
    #Добавление нового клиента
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO clients (surname, name, patronymic, phone) VALUES (%s, %s, %s, %s)",
                (surname, name, patronymic, phone)
            )
            conn.commit()
            return cursor.lastrowid


def update_client(client_id, surname, name, patronymic, phone):
    #Обновление информации о клиенте
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE clients SET surname=%s, name=%s, patronymic=%s, phone=%s WHERE id=%s",
                (surname, name, patronymic, phone, client_id)
            )
            conn.commit()
            return cursor.rowcount


def delete_client(client_id):
    #Удаление клиента
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM clients WHERE id=%s", (client_id,))
            conn.commit()
            return cursor.rowcount


# ========== УСЛУГИ ==========
def get_services():
    #Получение списка всех услуг с именем мастера
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT * FROM services;""")
            return cursor.fetchall()


def get_services_by_master(master_id):
    #Получение услуг конкретного мастера
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """SELECT services.id, services.name, services.duration, services.cost
            FROM services INNER JOIN master_services ON services.id = master_services.service_id
            WHERE master_services.master_id=%s 
            ORDER BY name;"""
            cursor.execute(query, (master_id,))
            return cursor.fetchall()


def add_service(name, duration, cost):
    #Добавление новой услуги
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO services (name, duration, cost) VALUES (%s, %s, %s)",
                (name, duration, cost)
            )
            conn.commit()
            return cursor.lastrowid


def update_service(service_id, name, duration, cost):
    #Обновление информации об услуге
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE services SET name=%s, duration=%s, cost=%s WHERE id=%s",
                (name, duration, cost, service_id)
            )
            conn.commit()


def delete_service(service_id):
    #Удаление услуги
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM services WHERE id=%s", (service_id,))
            conn.commit()
            return cursor.rowcount


# ========== РАСПИСАНИЕ МАСТЕРОВ ==========
def get_master_schedule(master_id, week_start_date):
    #Получение расписания мастера на неделю
    week_end_date = week_start_date + timedelta(days=6)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM master_schedule 
                WHERE master_id=%s AND work_date BETWEEN %s AND %s
                ORDER BY work_date
            """, (master_id, week_start_date, week_end_date))
            return cursor.fetchall()



def get_master_working_dates(master_id):
    #Получение всех дат, когда работает мастер
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT work_date FROM master_schedule 
                WHERE master_id=%s 
                ORDER BY work_date
            """, (master_id,))
            results = cursor.fetchall()
            return [row['work_date'] for row in results]


def get_master_schedule_for_date(master_id, work_date):
    #Получение расписания мастера на конкретную дату
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT start_time, end_time FROM master_schedule 
                WHERE master_id=%s AND work_date=%s
            """, (master_id, work_date))
            return cursor.fetchone()


# ========== ДОСТУПНОЕ ВРЕМЯ ==========
def get_available_time_slots(master_id, selected_date):
    #Получение доступных временных слотов мастера на выбранную дату
    with get_connection() as conn:
        cursor = conn.cursor()

        # Получаем расписание мастера на эту дату
        day_schedule_query = """SELECT start_time, end_time 
        FROM master_schedule 
        WHERE master_id=%s AND work_date=%s;"""
        cursor.execute(day_schedule_query, (master_id, selected_date))

        schedule = cursor.fetchone()

        if not schedule:
            return []  # Мастер не работает в этот день

        # Обрабатываем start_time и end_time
        start_time_str = timedelta_to_string(schedule["start_time"])
        end_time_str = timedelta_to_string(schedule["end_time"])

        start_time = datetime.strptime(start_time_str, '%H:%M')
        end_time = datetime.strptime(end_time_str, '%H:%M')

        # Получаем существующие записи на эту дату
        booked_times_query = """SELECT start_time, end_time 
        FROM appointments 
        WHERE master_id=%s AND appointment_date=%s AND status != 'Отменено';
        """
        cursor.execute(booked_times_query, (master_id, selected_date))

        booked_slots = [
            [datetime.strptime(timedelta_to_string(booked_time["start_time"]), '%H:%M'),
             datetime.strptime(timedelta_to_string(booked_time["end_time"]), '%H:%M')]
            for booked_time in cursor.fetchall()
        ]

        # Генерируем доступные слоты
        available_slots = []
        slot_duration = timedelta(minutes=30)

        while start_time + slot_duration <= end_time:
            slot_start = start_time
            slot_end = start_time + slot_duration

            # Проверяем, не занят ли слот
            for booked in booked_slots:
                start_book, end_book = booked
                # Слот доступен, если он полностью вне занятого интервала
                if not (slot_end <= start_book or slot_start >= end_book):
                    break
            else:
                available_slots.append({'start': slot_start.strftime('%H:%M'),'end': slot_end.strftime('%H:%M')})
            start_time += slot_duration

        return available_slots


# ========== ЗАПИСИ ==========
def get_appointments():
    #Получение всех записей с деталями
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, 
                       CONCAT(c.surname, ' ', c.name, ' ', COALESCE(c.patronymic, '')) as client_name,
                       c.phone as client_phone,
                       CONCAT(m.surname, ' ', m.name, ' ', COALESCE(m.patronymic, '')) as master_name,
                       s.name as service_name,
                       s.cost as service_price
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                ORDER BY a.appointment_date DESC, a.start_time DESC
            """)
            return cursor.fetchall()


# Возвращает записи между двумя датами
def appointments_between_date(start_date, end_date):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT a.*, 
        CONCAT(c.surname, ' ', c.name, ' ', COALESCE(c.patronymic, '')) as client_name,
        c.phone as client_phone,
        CONCAT(m.surname, ' ', m.name, ' ', COALESCE(m.patronymic, '')) as master_name,
        s.name as service_name,
        s.cost as service_price
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN masters m ON a.master_id = m.id
        JOIN services s ON a.service_id = s.id
        WHERE a.appointment_date BETWEEN %s AND %s
        ORDER BY a.appointment_date DESC, a.start_time DESC
        """
        cursor.execute(query, (start_date, end_date))
        return cursor.fetchall()


# Исправляем функцию get_appointments_by_date() в db.py:
def get_appointments_by_date(appointment_date):
    #Получение записей на конкретную дату
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, 
                       CONCAT(c.surname, ' ', c.name, ' ', COALESCE(c.patronymic, '')) as client_name,
                       CONCAT(m.surname, ' ', m.name, ' ', COALESCE(m.patronymic, '')) as master_name,
                       s.name as service_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.appointment_date=%s
                ORDER BY a.start_time
            """, (appointment_date,))
            return cursor.fetchall()


def get_appointment_by_id(appointment_id):
    #Получение записи по ID с деталями
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, 
                       CONCAT(c.surname, ' ', c.name, ' ', COALESCE(c.patronymic, '')) as client_name,
                       c.phone as client_phone,
                       CONCAT(m.surname, ' ', m.name, ' ', COALESCE(m.patronymic, '')) as master_name,
                       s.name as service_name,
                       s.cost as service_price,
                       s.duration as service_duration
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.id=%s
            """, (appointment_id,))
            return cursor.fetchone()


def add_appointment(client_id, master_id, service_id, appointment_date, start_time, end_time):
    """Добавление новой записи"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Получаем стоимость услуги
            cursor.execute("SELECT cost FROM services WHERE id=%s", (service_id,))
            service = cursor.fetchone()
            total_price = service['cost'] if service else 0

            cursor.execute("""
                INSERT INTO appointments 
                (client_id, master_id, service_id, appointment_date, start_time, end_time, total_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Ожидается')
            """, (client_id, master_id, service_id, appointment_date, start_time, end_time, total_price))

            conn.commit()
            return cursor.lastrowid


# def update_appointment(appointment_id, client_id, master_id, service_id, appointment_date, start_time, end_time,
#                        status):
#     """Обновление записи"""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             # Получаем стоимость услуги
#             cursor.execute("SELECT cost FROM services WHERE id=%s", (service_id,))
#             service = cursor.fetchone()
#             total_price = service['cost'] if service else 0
#
#             cursor.execute("""
#                 UPDATE appointments
#                 SET client_id=%s, master_id=%s, service_id=%s,
#                     appointment_date=%s, start_time=%s, end_time=%s,
#                     total_price=%s, status=%s
#                 WHERE id=%s
#             """, (client_id, master_id, service_id, appointment_date, start_time, end_time, total_price, status,
#                   appointment_id))
#
#             conn.commit()
#             return cursor.rowcount
#
#
# def delete_appointment(appointment_id):
#     """Удаление записи"""
#     with get_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute("DELETE FROM appointments WHERE id=%s", (appointment_id,))
#             conn.commit()
#             return cursor.rowcount


def cancel_appointment(appointment_id):
    """Отмена записи (изменение статуса на 'Отменено')"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE appointments 
                SET status='Отменено'
                WHERE id=%s
            """, (appointment_id,))
            conn.commit()



def complete_appointment(appointment_id):
    """Завершение записи (изменение статуса на 'Выполнено')"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE appointments 
                SET status='Выполнено', updated_at=NOW()
                WHERE id=%s
            """, (appointment_id,))
            conn.commit()
            return cursor.rowcount


def update_appointment_status_based_on_time():
    """Автоматическое обновление статусов записей на основе текущего времени"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            current_datetime = datetime.now()
            current_time = current_datetime.time()
            current_date = current_datetime.date()

            # Обновляем записи, время которых прошло и которые еще не завершены/отменены
            cursor.execute("""
                UPDATE appointments 
                SET status='Выполнено'
                WHERE appointment_date = %s 
                AND end_time <= %s 
                AND status = 'Ожидается'
            """, (current_date, current_time))

            updated_count = cursor.rowcount

            # Также обновляем записи, которые должны быть "В процессе"
            # (если текущее время между start_time и end_time)
            cursor.execute("""
                UPDATE appointments 
                SET status='В процессе'
                WHERE appointment_date = %s 
                AND start_time <= %s 
                AND end_time > %s 
                AND status = 'Ожидается'
            """, (current_date, current_time, current_time))

            updated_count += cursor.rowcount
            conn.commit()

            if updated_count > 0:
                print(f"Автоматически обновлено {updated_count} записей")

            return updated_count



# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========
def validate_phone(phone):
    """Проверка формата телефона"""
    import re
    pattern = r'^\+[0-9]{11}$'
    return re.match(pattern, phone) is not None


def format_client_name(client):
    """Форматирование имени клиента"""
    parts = []
    if client.get('surname'):
        parts.append(client['surname'])
    if client.get('name'):
        parts.append(client['name'])
    if client.get('patronymic'):
        parts.append(client['patronymic'])
    return ' '.join(parts) if parts else "Не указано"



def get_master_services(master_id):
    """Получение услуг, которые предоставляет конкретный мастер"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.* 
                FROM services s
                JOIN master_services ms ON s.id = ms.service_id
                WHERE ms.master_id = %s
                ORDER BY s.name
            """, (master_id,))
            return cursor.fetchall()

def add_master_service(master_id, service_id):
    """Добавление услуги мастеру"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO master_services (master_id, service_id) VALUES (%s, %s)",
                (master_id, service_id)
            )
            conn.commit()
            return cursor.lastrowid

def remove_master_service(master_id, service_id):
    """Удаление услуги у мастера"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM master_services WHERE master_id=%s AND service_id=%s",
                (master_id, service_id)
            )
            conn.commit()
            return cursor.rowcount

def get_all_master_services():
    """Получение всех связей мастеров и услуг"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ms.*, 
                       CONCAT(m.surname, ' ', m.name) as master_name,
                       s.name as service_name
                FROM master_services ms
                JOIN masters m ON ms.master_id = m.id
                JOIN services s ON ms.service_id = s.id
                ORDER BY master_name, service_name
            """)
            return cursor.fetchall()


#------------------------------------------------------------------------------Обновленные запросы----------------------------------------------------

def get_master_id_by_name(master_family: str, master_name: str) -> int:
    """Получение мастера по его полному имени. Используется в функции load_master_schedule | save_schedule | update_master_schedule"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT id FROM masters
        WHERE surname = %s AND name = %s;"""
        cursor.execute(query, (master_family, master_name))

        query_result = cursor.fetchall()

        master_id = query_result[0]["id"] if len(query_result) > 0 else None
        return master_id


def set_master_schedule(master_id: int, week_start: datetime, week_end: datetime, day_data: dict) -> None:
    """Установка расписания мастера на неделю используется в функции save_schedule"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Удаляем старое расписание на эти дни
        delete_query = """DELETE FROM master_schedule
        WHERE master_id=%s AND work_date BETWEEN %s AND %s;"""
        cursor.execute(delete_query, (master_id, week_start, week_end))

        # Сохраняем новое
        insert_query = """INSERT INTO master_schedule (master_id, day_of_week, work_date, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)"""
        for day_record in day_data:
            cursor.execute(insert_query, (master_id, day_record['day_of_week'], day_record['work_date'], day_record['start_time'], day_record['end_time']))

        # Фиксируем изменения в БД
        conn.commit()


def get_id_and_full_name_masters() -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT id, CONCAT(surname, ' ', name) AS full_name FROM masters;"""
        cursor.execute(query)
        return cursor.fetchall()


def get_unsetted_master_service(master_id: int) -> list:
    """Получаем все услуги, которые еще не были назачены мастеру"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT services.id, services.name, services.duration FROM services 
        WHERE services.id NOT IN 
        (SELECT master_services.service_id FROM master_services WHERE master_services.master_id = %s);"""
        cursor.execute(query, (master_id,))
        return cursor.fetchall()


def get_setted_master_service(master_id: int) -> list:
    """Получаем все услуги, которые были назначены мастеру"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT services.id, services.name, services.duration FROM services 
        WHERE services.id IN 
        (SELECT master_services.service_id FROM master_services WHERE master_services.master_id = %s);"""
        cursor.execute(query, (master_id,))
        return cursor.fetchall()


def set_master_service_to_db(master_id, service_id):
    """Устанавливаем мастеру услугу"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """INSERT INTO master_services(master_id, service_id) VALUES(%s, %s);"""
        cursor.execute(query, (master_id, service_id))
        conn.commit()


def unset_master_service_to_db(master_id, service_id):
    """Разрываем связь между мастером и услугой"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """DELETE FROM master_services WHERE master_id = %s AND service_id = %s;"""
        cursor.execute(query, (master_id, service_id))
        conn.commit()



def get_appointments_by_date_and_master(appointment_date, master_id) -> list:
    """Получение записей конкретного мастера на конкретную дату"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT a.*, 
                       CONCAT(c.surname, ' ', c.name, ' ', COALESCE(c.patronymic, '')) as client_name,
                       CONCAT(m.surname, ' ', m.name, ' ', COALESCE(m.patronymic, '')) as master_name,
                       s.name as service_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.appointment_date=%s AND a.master_id = %s
                ORDER BY a.start_time;
            """, (appointment_date, master_id))
        return cursor.fetchall()


def get_week_appointments(week_start, week_end) -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT appointment_date, start_time, end_time 
        FROM appointments 
        WHERE appointment_date >= %s AND appointment_date <= %s AND status != 'Отменено';
        """
        cursor.execute(query, (week_start, week_end))
        return cursor.fetchall()




#============================================================================================================
def get_attendance_statistics(start_date, end_date):
    """Статистика посещаемости за период (SQL версия)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Выполнено' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'Отменено' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN status = 'Ожидается' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'В процессе' THEN 1 ELSE 0 END) as in_progress
                FROM appointments 
                WHERE appointment_date BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchone()

def get_master_profit_report(start_date, end_date):
    """Прибыль по мастерам за период (SQL версия)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    CONCAT(m.surname, ' ', m.name) as master_name,
                    COUNT(*) as service_count,
                    SUM(a.total_price) as total_profit,
                    AVG(a.total_price) as avg_profit
                FROM appointments a
                JOIN masters m ON a.master_id = m.id
                WHERE a.status = 'Выполнено' 
                    AND a.appointment_date BETWEEN %s AND %s
                GROUP BY a.master_id, m.surname, m.name
                ORDER BY total_profit DESC
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()

def get_top_services_report(start_date, end_date):
    """Топ услуг за период (SQL версия)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    s.name as service_name,
                    COUNT(*) as service_count
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                WHERE a.status = 'Выполнено' 
                    AND a.appointment_date BETWEEN %s AND %s
                GROUP BY a.service_id, s.name
                ORDER BY service_count DESC
                LIMIT 5
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()

def get_master_load_report(start_date, end_date):
    """Загруженность мастеров за период (SQL версия)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    CONCAT(m.surname, ' ', m.name) as master_name,
                    a.status,
                    COUNT(*) as count
                FROM appointments a
                JOIN masters m ON a.master_id = m.id
                WHERE a.appointment_date BETWEEN %s AND %s 
                    AND a.status != 'Отменено'
                GROUP BY a.master_id, m.surname, m.name, a.status
                ORDER BY master_name, a.status
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()

def get_appointments_by_master_detailed(start_date, end_date):
    """Подробные записи по мастерам за период (SQL версия)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    CONCAT(m.surname, ' ', m.name) as master_name,
                    DATE(a.appointment_date) as appointment_day,
                    COUNT(*) as appointment_count
                FROM appointments a
                JOIN masters m ON a.master_id = m.id
                WHERE a.appointment_date BETWEEN %s AND %s
                GROUP BY a.master_id, m.surname, m.name, DATE(a.appointment_date)
                ORDER BY master_name, appointment_day
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchall()


