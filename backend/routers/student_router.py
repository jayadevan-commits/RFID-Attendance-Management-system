
from fastapi import APIRouter, HTTPException, status

from schemas.student_schema import (
    StudentCreate,
    StudentResponse
)

from services.student_service import (
    register_student,
    list_students,
    StudentConflict
)


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)
# @router.post(
#     "",
#     response_model=StudentResponse,
#     status_code=status.HTTP_201_CREATED
# )

@router.post(
    "",status_code=status.HTTP_201_CREATED
)
def create_student_api(student: StudentCreate):

    try:
        result = register_student(student)

        return {
            "success": True,
            "message": "Student registered successfully",
            "data": result
        }

    except StudentConflict as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )


@router.get("")
def get_students_api():

    students = list_students()

    return {
        "success": True,
        "message": "Students retrieved successfully",
        "data": students
    }
