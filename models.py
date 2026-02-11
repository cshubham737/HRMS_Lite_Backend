from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, description="Unique employee identifier")
    full_name: str = Field(..., min_length=2, description="Full name of employee")
    email: EmailStr = Field(..., description="Email address")
    department: Literal["Engineering", "HR", "Sales", "Marketing", "Finance", "Operations", "IT", "Other"]

    @field_validator('employee_id')
    @classmethod
    def employee_id_must_be_alphanumeric(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Employee ID cannot be empty')
        return v.strip().upper()

    @field_validator('full_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()


class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=2, description="Full name of employee")
    email: EmailStr = Field(..., description="Email address")
    department: Literal["Engineering", "HR", "Sales", "Marketing", "Finance", "Operations", "IT", "Other"]

    @field_validator('full_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()


class EmployeeResponse(EmployeeBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class AttendanceBase(BaseModel):
    employee_id: str = Field(..., description="Employee ID")
    date: str = Field(..., description="Attendance date (YYYY-MM-DD)")
    status: Literal["Present", "Absent"] = Field(..., description="Attendance status")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: str = Field(alias="_id")
    employee_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class AttendanceSummary(BaseModel):
    employee_id: str
    employee_name: str
    total_days: int
    total_present: int
    total_absent: int
    attendance_percentage: float


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[list] = None
