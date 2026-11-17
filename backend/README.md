# RFID Attendance Management System

A real-time RFID-based attendance management system that reads student
RFID cards using an ESP32-S3 and RC522 reader, publishes scan events
through MQTT, processes attendance with a FastAPI backend, stores
records in MySQL, and displays live attendance information in a React
dashboard.

## Features

-   RFID card scanning using ESP32-S3 and RC522.
-   MQTT-based communication between the device and backend.
-   Automatic student identification using registered card UIDs.
-   Automatic Punch In and Punch Out processing.
-   Multiple Punch In/Punch Out sessions per student per day.
-   Unknown card scans are recorded without creating attendance
    sessions.
-   MySQL storage for students, scan events, and attendance sessions.
-   REST API built with FastAPI.
-   React + Vite dashboard with automatic refresh.
-   Dashboard summary for present students, currently inside, completed
    sessions, and unknown scans.
-   Attendance session history with Punch In, Punch Out, and status.

## System Architecture

``` text
RFID Card
   |
   v
RC522 RFID Reader
   |
   v
ESP32-S3
   |
   | MQTT publish
   v
HiveMQ MQTT Broker
   |
   | MQTT subscribe
   v
Python MQTT Subscriber
   |
   v
FastAPI Backend
   |
   v
MySQL Database
   |
   | REST API
   v
React + Vite Dashboard
```

## Technology Stack

  Layer                  Technology
  ---------------------- ------------------------
  Microcontroller        ESP32-S3
  RFID reader            RC522
  Firmware development   Arduino IDE
  Device messaging       MQTT
  MQTT broker            HiveMQ
  Backend                Python, FastAPI
  MQTT client            Paho MQTT
  Database               MySQL
  Database connector     mysql-connector-python
  Frontend               React
  Frontend tooling       Vite

## Hardware Requirements

-   ESP32-S3 development board.
-   RC522 RFID reader module.
-   Compatible RFID cards or tags.
-   USB cable for programming and power.
-   Jumper wires.
-   Computer with Arduino IDE and Visual Studio Code.

### RC522 to ESP32-S3 Wiring

The following pin mapping is used by the current firmware:

  RC522 Pin     ESP32-S3 GPIO
  ----------- ---------------
  SDA / SS             GPIO 5
  SCK                 GPIO 12
  MOSI                GPIO 11
  MISO                GPIO 13
  RST                 GPIO 10
  3.3V                   3.3V
  GND                     GND
  IRQ           Not connected

**Important:** Power the RC522 module using 3.3V. Do not connect it to
5V.

## Software Requirements

Install the following software before running the project:

-   Python and pip.
-   Node.js and npm.
-   MySQL Server and MySQL Workbench (or another MySQL client).
-   Arduino IDE.
-   Visual Studio Code (recommended).
-   Git.

Install the Arduino libraries used by the firmware:

-   MFRC522
-   PubSubClient

## Project Structure

The project is organized into backend, firmware, and frontend folders.
The structure below represents the main files used in the application;
additional files may exist as the project grows.

``` text
RFID-Attendance/
├── backend/
│   ├── routers/
│   │   ├── scan_router.py
│   │   └── student_router.py
│   ├── main.py
│   ├── mqtt_subscriber.py
│   ├── database.py
│   ├── requirements.txt
│   └── .env
│
├── firmware/
│   └── rfid_attendance.ino
│
├── frontend/
│   ├── src/
│   │   └── ...
│   ├── package.json
│   └── ...
│
└── README.md
```

## Database Setup

1.  Start your MySQL server.
2.  Create the database:

``` sql
CREATE DATABASE rfid_attendance_db;
USE rfid_attendance_db;
```

3.  Create the students table:

``` sql
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(30) NOT NULL UNIQUE,
    card_uid VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

4.  Create the scan events table:

``` sql
CREATE TABLE scan_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    card_uid VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    student_id INT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_card_uid (card_uid),
    INDEX idx_received_at (received_at)
);
```

5.  Create the attendance sessions table:

``` sql
CREATE TABLE attendance_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    punch_in DATETIME NOT NULL,
    punch_out DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_student
        FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_student_date (student_id, attendance_date)
);
```

### Add sample students

Replace the card UIDs with the UIDs read from your own RFID cards.

``` sql
INSERT INTO students
    (student_name, roll_number, card_uid, department)
VALUES
    ('Arun Kumar', 'CS001', '84 00 30 8E', 'Computer Science'),
    ('Priya Lakshmi', 'CS002', 'B7 D1 02 A2', 'Computer Science');
```

Do not reuse these sample card UIDs unless they match your physical
cards.

## Backend Setup

Open a terminal and move into the backend folder:

``` powershell
cd backend
```

Create and activate a Python virtual environment:

``` powershell
python -m venv venv
.\venv\Scripts\activate
```

Install the Python dependencies:

``` powershell
pip install -r requirements.txt
```

The backend dependencies include:

``` text
fastapi
uvicorn
paho-mqtt==2.1.0
mysql-connector-python
python-dotenv
```

### Environment Configuration

Create a `.env` file inside the `backend` folder. Add your own MySQL and
MQTT configuration values. Never commit real passwords or private
credentials.

``` env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=rfid_attendance_db

MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC=jayadevan_attendance/device01/card_scan
```

The exact MQTT environment variable names must match the configuration
read by your current firmware and MQTT subscriber. If your code uses
constants instead, configure those values in the relevant source files.

Start the FastAPI server from the backend folder:

``` powershell
uvicorn main:app --reload
```

Backend base URL:

``` text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

``` text
http://127.0.0.1:8000/docs
```

Health endpoints:

-   `GET /` --- backend welcome/status response.
-   `GET /health` --- backend health check.
-   `GET /db-health` --- MySQL connection check.
-   `GET /dashboard/today` --- today's attendance dashboard data.

## MQTT Configuration

The current practice configuration uses:

  Setting     Value
  ----------- -------------------------------------------
  Broker      `broker.hivemq.com`
  Port        `1883`
  Topic       `jayadevan_attendance/device01/card_scan`
  Device ID   `ESP32_ATTENDANCE_01`

The ESP32 publishes a JSON message when an RFID card is scanned. Example
payload:

``` json
{
  "device_id": "ESP32_ATTENDANCE_01",
  "uid": "84 00 30 8E",
  "event": "CARD_SCANNED"
}
```

The Python MQTT subscriber listens to the configured topic, identifies
the student using the card UID, stores the scan event, and processes
attendance for registered students.

**Broker security note:** The public HiveMQ broker and unencrypted port
shown above are suitable for development and testing only. For
production, use a private broker or secured broker configuration with
authentication, TLS, access controls, and unique device credentials.

## Firmware Setup

1.  Open `firmware/rfid_attendance.ino` in Arduino IDE.
2.  Select the correct ESP32-S3 board and USB port.
3.  Install the MFRC522 and PubSubClient libraries.
4.  Configure the Wi-Fi SSID and password in the firmware.
5.  Configure the MQTT broker, port, and topic to match the backend
    subscriber.
6.  Verify the RC522 wiring.
7.  Upload the firmware to the ESP32-S3.
8.  Open Serial Monitor and select the baud rate configured in the
    sketch.
9.  Scan a registered RFID card and verify that the device publishes the
    scan event.

Do not commit Wi-Fi passwords, broker credentials, or other secrets to
GitHub.

## Frontend Setup

Open another terminal and move into the frontend folder:

``` powershell
cd frontend
```

Install frontend dependencies:

``` powershell
npm install
```

Start the Vite development server:

``` powershell
npm run dev
```

Open the local URL printed by Vite. The current development setup
normally uses:

``` text
http://localhost:5173
```

The React dashboard requests data from:

``` text
http://127.0.0.1:8000/dashboard/today
```

Make sure the backend is running and that its CORS configuration allows
the frontend development origin.

## Attendance Workflow

1.  A student taps an RFID card on the RC522 reader.
2.  The ESP32-S3 reads the card UID.
3.  The ESP32 publishes a `CARD_SCANNED` event to the MQTT topic.
4.  The Python MQTT subscriber receives the event.
5.  The backend looks up the UID in the `students` table.
6.  The scan event is stored in `scan_events`.
7.  If the card is registered, the attendance session is processed:
    -   If there is no open session for the student today, a new Punch
        In session is created.
    -   If the latest session is open, the scan records Punch Out.
    -   A later scan can create another Punch In session.
8.  The React dashboard fetches the latest dashboard data periodically
    and displays the updated attendance information.

Each student's attendance sessions are processed independently.

### Attendance Rules

The current backend attendance window is 09:00 AM to 06:00 PM.

-   Scans during the configured working window can create Punch In or
    Punch Out records.
-   Scans after the working window do not create attendance punches.
-   Unknown card UIDs are saved as scan events but do not create
    attendance sessions.
-   Each Punch In/Punch Out pair is stored as a separate row in
    `attendance_sessions`.
-   An open session has `punch_out = NULL`.

The dashboard presents open sessions as **Inside**. The requested UI
behavior is to show a punched-out session as **Outside** before 06:00 PM
and **Completed** at or after 06:00 PM. Confirm the current frontend
implementation if this display rule is changed.

## Dashboard API Response

`GET /dashboard/today` returns a response in this structure:

``` json
{
  "success": true,
  "message": "Today's attendance dashboard data retrieved",
  "data": {
    "summary": {
      "present_students": 2,
      "currently_inside": 1,
      "completed_sessions": 3,
      "unknown_scans": 0
    },
    "last_activity": {
      "id": 4,
      "student_name": "Priya Lakshmi",
      "roll_number": "CS002",
      "action": "PUNCH_IN",
      "activity_time": "2026-11-17T15:24:24"
    },
    "sessions": [
      {
        "id": 4,
        "student_id": 2,
        "student_name": "Priya Lakshmi",
        "roll_number": "CS002",
        "punch_in": "2026-11-17T15:24:24",
        "punch_out": null,
        "status": "INSIDE"
      }
    ]
  }
}
```

The values above are an example. Actual values depend on the database
records for the current date.

## Testing Checklist

-   [ ] ESP32-S3 connects to Wi-Fi.
-   [ ] RC522 detects an RFID card.
-   [ ] ESP32 publishes the scan event to MQTT.
-   [ ] Python MQTT subscriber receives the event.
-   [ ] Registered card UID identifies the correct student.
-   [ ] Scan event is inserted into `scan_events`.
-   [ ] First scan creates a Punch In session.
-   [ ] Second scan closes the open session with Punch Out.
-   [ ] A later scan creates a new session for the same student.
-   [ ] Unknown card scans are stored without attendance sessions.
-   [ ] `/dashboard/today` returns the expected JSON response.
-   [ ] React dashboard displays updated attendance data.
-   [ ] Dashboard refreshes automatically.

## Git and GitHub

Before pushing the project, create or update `.gitignore` at the project
root:

``` gitignore
# Python
__pycache__/
*.py[cod]
venv/
.env
.env.*

# Node
node_modules/
dist/

# IDE and operating system
.vscode/
.idea/
.DS_Store
Thumbs.db

# Arduino build artifacts
*.elf
*.bin
```

Review the files before committing to ensure that `.env`, Wi-Fi
credentials, database passwords, and private keys are not included.

Example Git commands:

``` bash
git init
git status
git add .
git status
git commit -m "Add RFID attendance management system"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

If the repository is already initialized and connected to GitHub, do not
run `git init` or add the remote again. Stage and commit only the
intended changes.

## Security and Deployment Notes

-   Do not commit secrets or real credentials.
-   Do not use the public MQTT broker configuration for production
    attendance data.
-   Configure production CORS origins instead of allowing development
    origins.
-   Use authenticated MQTT connections and TLS for production.
-   Protect student information and attendance records with appropriate
    access controls.
-   Use a production-ready database backup and recovery process.

## Current Project Scope

This repository documents the current RFID attendance workflow using
ESP32-S3, RC522, MQTT, FastAPI, MySQL, and React. Features not
implemented in the current source code should not be considered
available merely because they appear in this README.

## License

Add a license file if you intend to distribute or open-source this
project. Until a license is selected, all rights are reserved by the
project owner.
