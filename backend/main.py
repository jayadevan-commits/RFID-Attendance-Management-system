
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routers.scan_router import router as scan_router
from fastapi import FastAPI
from routers.student_router import router as student_router
from mqtt_subscriber import MQTTSubscriber
from database import get_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Start MQTT subscriber
    subscriber = MQTTSubscriber()
    subscriber.start()

    app.state.mqtt_subscriber = subscriber

    print("RFID Attendance Backend Started")

    yield

    # Stop MQTT subscriber
    subscriber.stop()

    print("RFID Attendance Backend Stopped")


app = FastAPI(
    title="RFID Attendance System",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router)
app.include_router(scan_router)

@app.get("/")
def home():

    return {
        "success": True,
        "message": "RFID Attendance API is running"
    }


@app.get("/health")
def health():

    return {
        "success": True,
        "message": "Backend is healthy"
    }

@app.get("/db-health")
def database_health():

    connection = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")

        result = cursor.fetchone()

        cursor.close()

        return {
            "success": True,
            "message": "MySQL connected successfully",
            "database": result[0]
        }

    except Exception:
        return {
            "success": False,
            "message": "MySQL connection failed"
        }

    finally:
        if connection and connection.is_connected():
            connection.close()