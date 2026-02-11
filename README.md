Backend – HRMS Lite

The backend is built using FastAPI with MongoDB as the database.
It provides REST APIs to manage employees, attendance, and dashboard statistics.


TECH STACK

- Python 3.10+
- FastAPI
- MongoDB (PyMongo)
- Pydantic (Validation)
- Uvicorn (ASGI Server)


LOCAL SETUP

1. Navigate to backend folder

cd backend

2. Create virtual environment

python -m venv venv

3. Activate virtual environment

Windows:
venv\Scripts\activate

macOS/Linux:
source venv/bin/activate

4. Install dependencies

pip install -r requirements.txt


ENVIRONMENT CONFIGURATION

Create a .env file inside backend folder and add:

MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=hrms_lite
ENVIRONMENT=development


RUN THE SERVER

uvicorn main:app --reload

API Base URL:
http://localhost:8000

Swagger Documentation:
http://localhost:8000/docs


API ENDPOINTS

Employees
- GET /api/employees
- GET /api/employees/{id}
- POST /api/employees
- DELETE /api/employees/{id}

Attendance
- GET /api/attendance
- GET /api/attendance/summary/{employee_id}
- POST /api/attendance
- DELETE /api/attendance/{id}

Dashboard
- GET /api/dashboard


KEY FEATURES

- Employee CRUD operations
- Attendance marking (one record per employee per day)
- Attendance filtering by employee and date
- Dashboard statistics (total employees, attendance count, today’s summary)
- Cascading delete (removes attendance when employee is deleted)
- Server-side validation using Pydantic


DEPLOYMENT (Example: Render)

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT

Environment Variable Required:
MONGODB_URL=<your-mongodb-connection-string>
