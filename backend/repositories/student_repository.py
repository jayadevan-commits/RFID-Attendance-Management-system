
from database import get_db_connection


def create_student(student):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO students
            (student_name, roll_number, card_uid, department)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                student.student_name,
                student.roll_number,
                student.card_uid,
                student.department
            )
        )

        student_id = cursor.lastrowid
        connection.commit()

        return student_id

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_all_students():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                student_name,
                roll_number,
                card_uid,
                department
            FROM students
            ORDER BY id DESC
        """

        cursor.execute(query)

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
