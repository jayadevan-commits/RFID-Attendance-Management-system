import { useEffect, useState } from "react";

const initials = (name = "") =>
  name
    .split(" ")
    .filter(Boolean)
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

function RfidIcon({ size = 24, color = "#fff", stroke = 2 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="6" width="14" height="12" rx="2" />
      <path d="M20 9a5 5 0 0 1 0 6" />
      <path d="M22 7a8 8 0 0 1 0 10" />
    </svg>
  );
}

const API_URL = "http://127.0.0.1:8000";

const formatTime = (value) => {
  if (!value) return "--";

  // API returns local MySQL DATETIME values without a timezone.
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";

  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
};

export default function RfidAttendance() {
  const [now, setNow] = useState(new Date());

  const [dashboard, setDashboard] = useState({
    summary: {
      present_students: 0,
      currently_inside: 0,
      completed_sessions: 0,
      unknown_scans: 0
    },
    last_activity: null,
    sessions: []
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Live clock
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch dashboard data from FastAPI
  useEffect(() => {
    let active = true;

    const fetchDashboard = async () => {
      try {
        const response = await fetch(`${API_URL}/dashboard/today`);

        if (!response.ok) {
          throw new Error(`Backend error: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success || !result.data) {
          throw new Error(result.message || "Unable to load dashboard");
        }

        if (active) {
          setDashboard({
            summary: {
              present_students: result.data.summary?.present_students ?? 0,
              currently_inside: result.data.summary?.currently_inside ?? 0,
              completed_sessions: result.data.summary?.completed_sessions ?? 0,
              unknown_scans: result.data.summary?.unknown_scans ?? 0
            },
            last_activity: result.data.last_activity ?? null,
            sessions: Array.isArray(result.data.sessions)
              ? result.data.sessions
              : []
          });
          setError("");
        }
      } catch (err) {
        if (active) {
          setError("Unable to connect to attendance backend.");
          console.error("Dashboard API error:", err);
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchDashboard();
    const interval = setInterval(fetchDashboard, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const { summary, last_activity, sessions } = dashboard;

  // A session stays labelled Outside until the 6:00 PM workday cutoff.
  // Open sessions remain Inside. After 6:00 PM, closed sessions become Completed.
  const isWorkdayComplete = now.getHours() > 18 ||
    (now.getHours() === 18 && now.getMinutes() >= 0);

  const getSessionStatus = (session) => {
    if (!session.punch_out) return "INSIDE";
    return isWorkdayComplete ? "COMPLETED" : "OUTSIDE";
  };

  return (
    <div className="ra-root">
      <style>{css}</style>

      <div className="ra-wrap">
        {/* Header */}
        <header className="ra-header">
          <div className="ra-brand">
            <div className="ra-logo"><RfidIcon /></div>
            <div>
              <div className="ra-title">RFID Attendance</div>
              <div className="ra-muted">Main Entrance · Reader 01</div>
            </div>
          </div>

          <div className="ra-clock">
            <div className="ra-time">
              {now.toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit"
              })}
            </div>
            <div className="ra-muted">
              {now.toLocaleDateString("en-GB", {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric"
              })}
            </div>
          </div>
        </header>

        <main className="ra-main">
          {/* Left section */}
          <section className="ra-left">
            <div className="ra-scan">
              <div className="ra-scan-icon">
                <RfidIcon size={48} color="#0F766E" stroke={1.8} />
              </div>
              <div className="ra-scan-title">Tap your card</div>
              <div className="ra-muted ra-center">
                Hold your RFID card near the reader
                <br />
                to scan automatically
              </div>
              <span className="ra-pill ra-pill-ok">RFID Reader Active</span>

              {loading && (
                <div className="ra-muted">Loading attendance data...</div>
              )}
              {error && <div className="ra-error" role="alert">{error}</div>}
            </div>

            {/* Last attendance activity */}
            <div className="ra-card ra-last">
              <div className="ra-row-between">
                <div className="ra-label">LAST ATTENDANCE ACTIVITY</div>
                {last_activity && (
                  <span className={`ra-pill ${
                    last_activity.action === "PUNCH_IN" ? "ra-pill-ok" : "ra-pill-out"
                  }`}>
                    {last_activity.action === "PUNCH_IN" ? "Punch In" : "Punch Out"}
                  </span>
                )}
              </div>

              {last_activity ? (
                <>
                  <div className="ra-person">
                    <div className="ra-avatar">
                      {initials(last_activity.student_name)}
                    </div>
                    <div>
                      <div className="ra-name">{last_activity.student_name}</div>
                      <div className="ra-muted">
                        Roll No: {last_activity.roll_number || "--"}
                      </div>
                    </div>
                  </div>
                  <div className="ra-muted">
                    Activity time: {formatTime(last_activity.activity_time)}
                  </div>
                </>
              ) : (
                <div className="ra-empty">No attendance activity recorded today.</div>
              )}
            </div>
          </section>

          {/* Right section */}
          <section className="ra-right">
            <div className="ra-stats">
              <Stat label="Present Students" value={summary.present_students} color="#0F766E" />
              <Stat label="Currently Inside" value={summary.currently_inside} color="#0F766E" />
              <Stat label="Punch-out Sessions" value={summary.completed_sessions} color="#14213D" />
              <Stat label="Unknown Scans" value={summary.unknown_scans} color="#B42318" />
            </div>

            {/* Today's attendance sessions */}
            <div className="ra-card ra-log">
              <div className="ra-section-heading">
                <h2 className="ra-log-title">Today's Attendance Sessions</h2>
                <span className="ra-session-count">{sessions.length} records</span>
              </div>

              <div className="ra-table-wrap">
                <table className="ra-table">
                  <thead>
                    <tr>
                      <th>NAME</th>
                      <th>ROLL NO</th>
                      <th>PUNCH IN</th>
                      <th>PUNCH OUT</th>
                      <th className="ra-right-align">STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="ra-muted-cell ra-empty-cell">
                          {loading
                            ? "Loading attendance records..."
                            : "No attendance sessions recorded today."}
                        </td>
                      </tr>
                    ) : (
                      sessions.map((session) => (
                        <tr key={session.id}>
                          <td className="ra-bold">{session.student_name || "--"}</td>
                          <td className="ra-muted-cell">{session.roll_number || "--"}</td>
                          <td className="ra-muted-cell">{formatTime(session.punch_in)}</td>
                          <td className="ra-muted-cell">{formatTime(session.punch_out)}</td>
                          <td className="ra-right-align">
                            {(() => {
                              const displayStatus = getSessionStatus(session);
                              const statusClass =
                                displayStatus === "INSIDE"
                                  ? "ra-pill-ok"
                                  : displayStatus === "OUTSIDE"
                                    ? "ra-pill-outside"
                                    : "ra-pill-completed";

                              return (
                                <span className={`ra-pill ${statusClass}`}>
                                  {displayStatus === "INSIDE"
                                    ? "Inside"
                                    : displayStatus === "OUTSIDE"
                                      ? "Outside"
                                      : "Completed"}
                                </span>
                              );
                            })()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div className="ra-card ra-stat">
      <div className="ra-muted">{label}</div>
      <div className="ra-stat-value" style={{ color }}>{value}</div>
    </div>
  );
}

const css = `
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
.ra-root{min-height:100vh;box-sizing:border-box;background:#f3f8f6;color:#17352f;font-family:Inter,Arial,sans-serif;padding:34px 40px}
.ra-root *{box-sizing:border-box}
.ra-wrap{width:100%;max-width:1420px;margin:0 auto;display:flex;flex-direction:column;gap:28px}
.ra-header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:18px;padding:4px 2px}
.ra-brand{display:flex;align-items:center;gap:14px}
.ra-logo{width:48px;height:48px;border-radius:15px;background:#087f68;display:flex;align-items:center;justify-content:center;box-shadow:0 5px 14px rgba(8,127,104,.16)}
.ra-title{font-size:22px;font-weight:800;letter-spacing:-.5px;color:#123b32}
.ra-muted{font-size:13px;line-height:1.5;color:#71827d}
.ra-center{text-align:center}
.ra-clock{text-align:right}
.ra-time{font-size:30px;font-weight:800;letter-spacing:-.8px;color:#123b32}
.ra-main{display:grid;grid-template-columns:minmax(300px,.82fr) minmax(0,1.55fr);gap:24px;align-items:start}
.ra-left,.ra-right{min-width:0;display:flex;flex-direction:column;gap:20px}
.ra-card{background:#fff;border:1px solid #e5efeb;border-radius:20px;padding:25px;box-shadow:0 5px 20px rgba(28,75,62,.045)}
.ra-scan{position:relative;min-height:270px;background:#fff;border-radius:20px;padding:32px 28px;border:1.5px dashed #48a995;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;box-shadow:0 5px 20px rgba(28,75,62,.035)}
.ra-scan-icon{width:88px;height:88px;border-radius:50%;background:#e8f6f1;display:flex;align-items:center;justify-content:center}
.ra-scan-title{font-size:23px;font-weight:800;letter-spacing:-.4px;color:#173d34}
.ra-hidden-input{position:absolute;opacity:0;pointer-events:none;width:1px;height:1px}
.ra-error{font-size:13px;font-weight:600;color:#b42318;background:#fff1f0;border-radius:10px;padding:9px 12px}
.ra-last{display:flex;flex-direction:column;gap:17px}
.ra-row-between{display:flex;align-items:center;justify-content:space-between;gap:12px}
.ra-label{font-size:11px;font-weight:800;letter-spacing:.8px;color:#71827d}
.ra-person{display:flex;align-items:center;gap:15px}
.ra-avatar{width:58px;height:58px;flex-shrink:0;border-radius:17px;background:#e5f4ef;color:#087f68;display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:800}
.ra-name{font-size:18px;font-weight:800;color:#173d34}
.ra-pill{display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;letter-spacing:.1px;padding:6px 11px;border-radius:999px;white-space:nowrap}
.ra-pill-ok{color:#08735e;background:#e1f5ed}
.ra-pill-out{color:#08735e;background:#e8f4f0}
.ra-pill-outside{color:#b42318;background:#feeceb}
.ra-pill-completed{color:#42645a;background:#edf3f0}
.ra-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.ra-stat{min-width:0;border-radius:17px;padding:19px 18px}
.ra-stat-value{font-size:30px;font-weight:800;letter-spacing:-.7px;margin-top:8px}
.ra-log{min-width:0;padding:24px 25px}
.ra-section-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}
.ra-log-title{margin:0;font-size:18px;font-weight:800;letter-spacing:-.3px;color:#173d34}
.ra-session-count{font-size:12px;font-weight:600;color:#71827d;white-space:nowrap;background:#f1f7f4;padding:6px 10px;border-radius:999px}
.ra-table-wrap{width:100%;overflow-x:auto}
.ra-table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;min-width:620px}
.ra-table th{text-align:left;font-size:10px;font-weight:800;letter-spacing:.65px;color:#82918c;padding:12px 10px;border-bottom:1px solid #e8efec;white-space:nowrap}
.ra-table td{padding:15px 10px;border-bottom:1px solid #edf2ef;white-space:nowrap;color:#526a62}
.ra-table tbody tr:hover{background:#f8fbf9}
.ra-table tr:last-child td{border-bottom:none}
.ra-right-align{text-align:right!important}
.ra-bold{font-weight:700!important;color:#24483e!important}
.ra-muted-cell{color:#71827d}
.ra-empty,.ra-empty-cell{color:#71827d;font-size:13px}
.ra-empty-cell{text-align:center;padding:30px 8px!important}
@media (max-width:1100px){.ra-root{padding:28px 24px}.ra-main{grid-template-columns:minmax(260px,.8fr) minmax(0,1.4fr)}.ra-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:760px){.ra-root{padding:18px 14px}.ra-main{grid-template-columns:1fr}.ra-clock{text-align:left}.ra-header{align-items:flex-start;flex-direction:column}.ra-card{padding:20px}.ra-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.ra-section-heading{align-items:flex-start}}
@media (max-width:380px){.ra-stats{grid-template-columns:1fr 1fr}.ra-stat{padding:15px}.ra-stat-value{font-size:26px}}
`;
