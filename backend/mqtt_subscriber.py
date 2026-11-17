
import json
import logging
from datetime import datetime, time

import mysql.connector
import paho.mqtt.client as mqtt

from database import get_db_connection


MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "jayadevan_attendance/device01/card_scan"

WORK_START = time(9, 0)
WORK_END = time(18, 0)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_uid(uid):
    """Convert RFID UID into a consistent format."""

    cleaned = (
        uid.upper()
        .replace(":", "")
        .replace("-", "")
        .replace(" ", "")
    )

    if not cleaned or len(cleaned) % 2 != 0:
        raise ValueError("Invalid RFID UID format")

    return " ".join(
        cleaned[i:i + 2]
        for i in range(0, len(cleaned), 2)
    )


class MQTTSubscriber:

    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="rfid-attendance-python-01"
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code == 0:
            logger.info("MQTT Connected Successfully")
            client.subscribe(MQTT_TOPIC, qos=1)
            logger.info("Subscribed to: %s", MQTT_TOPIC)

        else:
            logger.error("MQTT Connection Failed: %s", reason_code)

    def save_scan_event(self, cursor, device_id, uid, event_type, student_id):

        query = """
            INSERT INTO scan_events
            (device_id, card_uid, event_type, student_id)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (device_id, uid, event_type, student_id)
        )

    def process_attendance(self, cursor, student_id):

        now = datetime.now()
        current_time = now.time()
        today = now.date()

        # Check working hours
        if not (WORK_START <= current_time <= WORK_END):
            logger.warning(
                "Attendance rejected. Outside working hours: %s",
                now.strftime("%I:%M:%S %p")
            )
            return "OUTSIDE_WORKING_HOURS"

        # Lock this student's session records for today.
        lock_query = """
            SELECT id, punch_in, punch_out
            FROM attendance_sessions
            WHERE student_id = %s
              AND attendance_date = %s
            ORDER BY id DESC
            LIMIT 1
            FOR UPDATE
        """

        cursor.execute(lock_query, (student_id, today))
        session = cursor.fetchone()

        # No session exists, or previous session is closed.
        if session is None or session[2] is not None:

            insert_query = """
                INSERT INTO attendance_sessions
                (student_id, attendance_date, punch_in)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                insert_query,
                (student_id, today, now)
            )

            logger.info(
                "PUNCH IN recorded at %s",
                now.strftime("%I:%M:%S %p")
            )

            return "PUNCH_IN"

        # An open session exists. Record Punch Out.
        session_id = session[0]

        update_query = """
            UPDATE attendance_sessions
            SET punch_out = %s
            WHERE id = %s
              AND punch_out IS NULL
        """

        cursor.execute(update_query, (now, session_id))

        logger.info(
            "PUNCH OUT recorded at %s",
            now.strftime("%I:%M:%S %p")
        )

        return "PUNCH_OUT"

    # def save_scan_event(self, cursor, device_id, uid, event_type, student_id):

    #     query = """
    #         INSERT INTO scan_events
    #         (device_id, card_uid, event_type, student_id)
    #         VALUES (%s, %s, %s, %s)
    #     """

    #     cursor.execute(
    #         query,
    #         (device_id, uid, event_type, student_id)
    #     )

    def handle_scan(self, device_id, uid, event_type):

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            connection.start_transaction()

            cursor = connection.cursor()

            # Identify student.
            student_query = """
                SELECT id, student_name, roll_number
                FROM students
                WHERE card_uid = %s
                LIMIT 1
                FOR UPDATE
            """

            cursor.execute(student_query, (uid,))
            student = cursor.fetchone()

            student_id = None

            if student:
                student_id = student[0]

                logger.info("Student Identified")
                logger.info("Student ID: %s", student_id)
                logger.info("Student Name: %s", student[1])
                logger.info("Roll Number: %s", student[2])

            else:
                logger.warning("Unknown RFID card: %s", uid)

            # Always save the scan event.
            self.save_scan_event(
                cursor,
                device_id,
                uid,
                event_type,
                student_id
            )

            # Only registered students get attendance.
            if student_id is not None:

                result = self.process_attendance(
                    cursor,
                    student_id
                )

                logger.info("Attendance result: %s", result)

            connection.commit()

            logger.info("Scan event successfully stored")

            return True

        except Exception:
            if connection and connection.is_connected():
                connection.rollback()

            logger.exception("Error processing RFID scan")
            return False

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    def on_message(self, client, userdata, message):

        try:
            payload = message.payload.decode("utf-8")
            data = json.loads(payload)

            device_id = data.get("device_id")
            raw_uid = data.get("uid")
            event_type = data.get("event")

            if not all([device_id, raw_uid, event_type]):
                logger.warning("MQTT message missing required fields")
                return

            uid = normalize_uid(raw_uid)

            logger.info("RFID CARD RECEIVED")
            logger.info("Device ID: %s", device_id)
            logger.info("Card UID: %s", uid)
            logger.info("Event: %s", event_type)

            self.handle_scan(device_id, uid, event_type)

        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            logger.exception("Invalid MQTT message")

    def start(self):

        self.client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            keepalive=60
        )

        self.client.loop_start()
        logger.info("MQTT Subscriber Started")

    def stop(self):

        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT Subscriber Stopped")


if __name__ == "__main__":

    subscriber = MQTTSubscriber()

    try:
        subscriber.start()

        while True:
            pass

    except KeyboardInterrupt:
        subscriber.stop()
