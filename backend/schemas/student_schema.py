
from pydantic import BaseModel, Field, field_validator


class StudentCreate(BaseModel):
    student_name: str = Field(min_length=2, max_length=100)
    roll_number: str = Field(min_length=1, max_length=30)
    card_uid: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=100)

    @field_validator("student_name", "roll_number")
    @classmethod
    def clean_text(cls, value):
        return value.strip()

    @field_validator("card_uid")
    @classmethod
    def normalize_uid(cls, value):
        cleaned = (
            value.strip()
            .upper()
            .replace(":", "")
            .replace("-", "")
            .replace(" ", "")
        )

        if not cleaned or len(cleaned) % 2 != 0:
            raise ValueError("Invalid RFID card UID")

        return " ".join(
            cleaned[i:i + 2]
            for i in range(0, len(cleaned), 2)
        )


class StudentResponse(BaseModel):
    id: int
    student_name: str
    roll_number: str
    card_uid: str
    department: str | None
