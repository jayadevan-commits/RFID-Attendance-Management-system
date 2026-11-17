
import mysql.connector

from schemas.student_schema import StudentCreate
from repositories.student_repository import (
    create_student,
    get_all_students
)


class StudentConflict(Exception):
    pass


def register_student(student: StudentCreate):

    try:
        student_id = create_student(student)

        return {
            "id": student_id,
            "student_name": student.student_name,
            "roll_number": student.roll_number,
            "card_uid": student.card_uid,
            "department": student.department
        }

    except mysql.connector.IntegrityError as error:
        if error.errno == 1062:
            raise StudentConflict(
                "Roll number or RFID card UID already registered"
            )

        raise


def list_students():
    return get_all_students()
