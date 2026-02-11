from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime
from bson import ObjectId
import os
import traceback

from database import get_database, connect_to_mongo, close_mongo_connection
from models import EmployeeCreate, AttendanceCreate

app = FastAPI(
    title="HRMS Lite API",
    description="Human Resource Management System API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "HRMS Lite API",
        "version": "1.0.0",
        "endpoints": {
            "employees": "/api/employees",
            "attendance": "/api/attendance",
            "docs": "/docs"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    try:
        db = get_database()
        db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ==================== EMPLOYEE ENDPOINTS ====================

@app.get("/api/employees")
async def get_all_employees():
    """Get all employees"""
    try:
        db = get_database()
        employees = list(db.employees.find().sort("created_at", -1))
        
        for emp in employees:
            emp["_id"] = str(emp["_id"])
        
        return {
            "success": True,
            "count": len(employees),
            "data": employees
        }
    except Exception as e:
        print(f"Error in get_all_employees: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )

@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: str):
    """Get a specific employee by ID"""
    try:
        db = get_database()
        
        if ObjectId.is_valid(employee_id):
            employee = db.employees.find_one({"_id": ObjectId(employee_id)})
        else:
            employee = db.employees.find_one({"employee_id": employee_id.upper()})
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        employee["_id"] = str(employee["_id"])
        
        return {
            "success": True,
            "data": employee
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employee: {str(e)}"
        )

@app.post("/api/employees", status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    """Create a new employee with auto-generated ID"""
    try:
        db = get_database()
        
        # Auto-generate Employee ID
        last_employee = db.employees.find_one(sort=[("employee_id", -1)])
        
        if last_employee and "employee_id" in last_employee:
            # Extract number from last ID (e.g., "EMP005" -> 5)
            try:
                last_id_num = int(last_employee["employee_id"].replace("EMP", ""))
                new_id_num = last_id_num + 1
            except:
                new_id_num = 1
        else:
            new_id_num = 1
        
        # Format as EMP001, EMP002, etc.
        auto_employee_id = f"EMP{new_id_num:03d}"
        
        # Check if email already exists
        existing_email = db.employees.find_one({"email": employee.email.lower()})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Create employee document
        employee_dict = {
            "employee_id": auto_employee_id,
            "full_name": employee.full_name.strip(),
            "email": employee.email.lower(),
            "department": employee.department,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.employees.insert_one(employee_dict)
        employee_dict["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "message": f"Employee created successfully with ID: {auto_employee_id}",
            "data": employee_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_employee: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employee: {str(e)}"
        )

@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Delete an employee and their attendance records"""
    try:
        db = get_database()
        
        if ObjectId.is_valid(employee_id):
            employee = db.employees.find_one({"_id": ObjectId(employee_id)})
            query = {"_id": ObjectId(employee_id)}
        else:
            employee = db.employees.find_one({"employee_id": employee_id.upper()})
            query = {"employee_id": employee_id.upper()}
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Delete attendance records
        db.attendance.delete_many({"employee_id": employee["employee_id"]})
        
        # Delete employee
        db.employees.delete_one(query)
        
        return {
            "success": True,
            "message": "Employee and associated attendance records deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employee: {str(e)}"
        )

# ==================== ATTENDANCE ENDPOINTS ====================

@app.get("/api/attendance")
async def get_all_attendance(
    employee_id: Optional[str] = None,
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get attendance records with optional filters"""
    try:
        db = get_database()
        query = {}
        
        if employee_id:
            query["employee_id"] = employee_id.upper()
        
        if date:
            query["date"] = date
        elif start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        
        attendance_records = list(db.attendance.find(query).sort("date", -1))
        
        for record in attendance_records:
            record["_id"] = str(record["_id"])
            employee = db.employees.find_one({"employee_id": record["employee_id"]})
            record["employee_name"] = employee["full_name"] if employee else "Unknown"
        
        return {
            "success": True,
            "count": len(attendance_records),
            "data": attendance_records
        }
    except Exception as e:
        print(f"Error in get_all_attendance: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance records: {str(e)}"
        )

@app.get("/api/attendance/summary/{employee_id}")
async def get_attendance_summary(employee_id: str):
    """Get attendance summary for an employee"""
    try:
        db = get_database()
        
        employee = db.employees.find_one({"employee_id": employee_id.upper()})
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        attendance_records = list(db.attendance.find({"employee_id": employee_id.upper()}))
        
        total_days = len(attendance_records)
        total_present = sum(1 for record in attendance_records if record["status"] == "Present")
        total_absent = sum(1 for record in attendance_records if record["status"] == "Absent")
        attendance_percentage = (total_present / total_days * 100) if total_days > 0 else 0
        
        return {
            "success": True,
            "data": {
                "employee_id": employee_id.upper(),
                "employee_name": employee["full_name"],
                "total_days": total_days,
                "total_present": total_present,
                "total_absent": total_absent,
                "attendance_percentage": round(attendance_percentage, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_attendance_summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance summary: {str(e)}"
        )

@app.post("/api/attendance", status_code=status.HTTP_201_CREATED)
async def mark_attendance(attendance: AttendanceCreate):
    """Mark or update attendance for an employee"""
    try:
        db = get_database()
        
        employee = db.employees.find_one({"employee_id": attendance.employee_id.upper()})
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        attendance_date = attendance.date
        # Check if attendance already exists for this date
        existing_attendance = db.attendance.find_one({
            "employee_id": attendance.employee_id.upper(),
            "date": attendance_date
        })
        
        if existing_attendance:
            # Update existing
            db.attendance.update_one(
                {"_id": existing_attendance["_id"]},
                {
                    "$set": {
                        "status": attendance.status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            existing_attendance["_id"] = str(existing_attendance["_id"])
            existing_attendance["status"] = attendance.status
            existing_attendance["employee_name"] = employee["full_name"]
            
            return {
                "success": True,
                "message": "Attendance updated successfully",
                "data": existing_attendance
            }
        
        # Create new
        attendance_dict = {
            "employee_id": attendance.employee_id.upper(),
            "date": attendance_date,
            "status": attendance.status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.attendance.insert_one(attendance_dict)
        attendance_dict["_id"] = str(result.inserted_id)
        attendance_dict["employee_name"] = employee["full_name"]
        
        return {
            "success": True,
            "message": "Attendance marked successfully",
            "data": attendance_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in mark_attendance: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking attendance: {str(e)}"
        )

@app.delete("/api/attendance/{attendance_id}")
async def delete_attendance(attendance_id: str):
    """Delete an attendance record"""
    try:
        db = get_database()
        
        if not ObjectId.is_valid(attendance_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid attendance ID"
            )
        
        result = db.attendance.delete_one({"_id": ObjectId(attendance_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        return {
            "success": True,
            "message": "Attendance record deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting attendance record: {str(e)}"
        )

# ==================== DASHBOARD ENDPOINT ====================

@app.get("/api/dashboard")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        db = get_database()
        
        total_employees = db.employees.count_documents({})
        total_attendance_records = db.attendance.count_documents({})
        
        # Get today's attendance
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_present = db.attendance.count_documents({"date": today, "status": "Present"})
        today_absent = db.attendance.count_documents({"date": today, "status": "Absent"})
        
        return {
            "success": True,
            "data": {
                "total_employees": total_employees,
                "total_attendance_records": total_attendance_records,
                "today_present": today_present,
                "today_absent": today_absent,
                "today_date": today
            }
        }
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)