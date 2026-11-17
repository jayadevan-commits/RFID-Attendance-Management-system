
from fastapi import APIRouter
from database import get_db_connection

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/today")
def get_today_dashboard():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Today's attendance sessions
        session_query = """
            SELECT
                ats.id,
                ats.student_id,
                s.student_name,
                s.roll_number,
                DATE_FORMAT(
                    ats.punch_in,
                    '%Y-%m-%dT%H:%i:%s'
                ) AS punch_in,
                DATE_FORMAT(
                    ats.punch_out,
                    '%Y-%m-%dT%H:%i:%s'
                ) AS punch_out,
                CASE
                    WHEN ats.punch_out IS NULL THEN 'INSIDE'
                    ELSE 'COMPLETED'
                END AS status
            FROM attendance_sessions ats
            INNER JOIN students s
                ON ats.student_id = s.id
            WHERE ats.attendance_date = CURDATE()
            ORDER BY ats.id DESC
        """

        cursor.execute(session_query)
        sessions = cursor.fetchall()

        # 2. Attendance summary
        attendance_summary_query = """
            SELECT
                COUNT(DISTINCT student_id) AS present_students,

                COUNT(DISTINCT CASE
                    WHEN punch_out IS NULL THEN student_id
                END) AS currently_inside,

                SUM(CASE
                    WHEN punch_out IS NOT NULL THEN 1
                    ELSE 0
                END) AS completed_sessions

            FROM attendance_sessions
            WHERE attendance_date = CURDATE()
        """

        cursor.execute(attendance_summary_query)
        attendance_summary = cursor.fetchone()

        # 3. Unknown card scans
        unknown_query = """
            SELECT COUNT(*) AS unknown_scans
            FROM scan_events
            WHERE student_id IS NULL
              AND DATE(received_at) = CURDATE()
        """

        cursor.execute(unknown_query)
        unknown_result = cursor.fetchone()

        # 4. Last attendance activity
        last_activity_query = """
            SELECT
                ats.id,
                s.student_name,
                s.roll_number,
                CASE
                    WHEN ats.punch_out IS NULL THEN 'PUNCH_IN'
                    ELSE 'PUNCH_OUT'
                END AS action,
                DATE_FORMAT(
                    CASE
                        WHEN ats.punch_out IS NULL
                        THEN ats.punch_in
                        ELSE ats.punch_out
                    END,
                    '%Y-%m-%dT%H:%i:%s'
                ) AS activity_time
            FROM attendance_sessions ats
            INNER JOIN students s
                ON ats.student_id = s.id
            WHERE ats.attendance_date = CURDATE()
            ORDER BY
                GREATEST(
                    ats.punch_in,
                    COALESCE(ats.punch_out, ats.punch_in)
                ) DESC,
                ats.id DESC
            LIMIT 1
        """

        cursor.execute(last_activity_query)
        last_activity = cursor.fetchone()

        return {
            "success": True,
            "message": "Today's attendance dashboard data retrieved",
            "data": {
                "summary": {
                    "present_students":
                        attendance_summary["present_students"] or 0,

                    "currently_inside":
                        attendance_summary["currently_inside"] or 0,

                    "completed_sessions":
                        attendance_summary["completed_sessions"] or 0,

                    "unknown_scans":
                        unknown_result["unknown_scans"] or 0
                },
                "last_activity": last_activity,
                "sessions": sessions
            }
        }

    except Exception as e:
        print("Dashboard API Error:", e)

        return {
            "success": False,
            "message": "Unable to retrieve dashboard data",
            "data": None
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
