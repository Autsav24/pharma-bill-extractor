import streamlit as st
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="📅", layout="wide")

APPOINTMENT_FILE = "appointments.xlsx"

st.title("🏥 Buddha Clinic - Appointment System")

# ----------------- Helpers -----------------
def valid_mobile(m: str) -> bool:
    m = m.strip().replace(" ", "").replace("-", "")
    return m.isdigit() and (len(m) in (10, 12))

def wa_link(number: str, text: str) -> str:
    num = number.strip().replace(" ", "").replace("-", "")
    if len(num) == 10:
        num = "91" + num
    return f"https://wa.me/{num}?text={urllib.parse.quote(text)}"

def load_appointments() -> pd.DataFrame:
    if os.path.exists(APPOINTMENT_FILE):
        return pd.read_excel(APPOINTMENT_FILE)
    return pd.DataFrame(columns=[
        "Name","Age","Gender","Mobile",
        "AppointmentDate","AppointmentTime","Doctor","Notes","Status","BookedOn"
    ])

def save_appointments(df: pd.DataFrame):
    df.to_excel(APPOINTMENT_FILE, index=False)

# ----------------- Dashboard Mode -----------------
role = st.radio("👥 Select Role", ["Reception/Staff", "Doctor"])

if role == "Doctor":
    selected_doctor = st.selectbox("Select Doctor", ["Dr. Ankur Poddar"])  # later add more doctors
else:
    selected_doctor = None

# ----------------- Booking Form (Reception Only) -----------------
if role == "Reception/Staff":
    st.subheader("📌 Book a New Appointment")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        notes = st.text_area("Notes / Reason for Visit")
    with col2:
        mobile = st.text_input("Mobile Number")
        appt_date = st.date_input("Appointment Date", datetime.today())
        appt_time = st.time_input("Appointment Time")
        doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

    if st.button("✅ Book Appointment"):
        if not name or not mobile:
            st.error("⚠️ Name and Mobile required")
        elif not valid_mobile(mobile):
            st.error("⚠️ Invalid mobile number")
        else:
            df = load_appointments()
            date_str = appt_date.strftime("%Y-%m-%d")
            time_str = appt_time.strftime("%H:%M")

            new_entry = pd.DataFrame([{
                "Name": name,
                "Age": age,
                "Gender": gender,
                "Mobile": mobile.strip(),
                "AppointmentDate": date_str,
                "AppointmentTime": time_str,
                "Doctor": doctor,
                "Notes": notes,
                "Status": "Booked",
                "BookedOn": datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            save_appointments(df)

            st.success(f"✅ Appointment booked for {name} with {doctor} on {date_str} at {time_str}")

            msg = f"Hello {name}, your appointment with {doctor} is confirmed on {date_str} at {time_str}. - Buddha Clinic"
            st.markdown(f"[📲 Send WhatsApp Confirmation]({wa_link(mobile, msg)})", unsafe_allow_html=True)

# ----------------- Appointment Management -----------------
st.subheader("🛠 Manage Appointments")

df = load_appointments()

# Filter by doctor if in doctor mode
if selected_doctor:
    df = df[df["Doctor"] == selected_doctor]

if not df.empty:
    search = st.text_input("🔍 Search by name or mobile")
    if search:
        df = df[df["Name"].str.contains(search, case=False) | df["Mobile"].astype(str).str.contains(search)]

    st.dataframe(df, use_container_width=True)

    if role == "Reception/Staff":
        selected = st.selectbox("Select appointment to update", df.index.astype(str))
        if selected:
            selected_idx = int(selected)
            st.write("Editing:", df.loc[selected_idx, "Name"], "-", df.loc[selected_idx, "AppointmentDate"], df.loc[selected_idx, "AppointmentTime"])

            action = st.radio("Action", ["Cancel", "Reschedule"])
            if action == "Cancel":
                if st.button("❌ Cancel Appointment"):
                    df.at[selected_idx, "Status"] = "Cancelled"
                    save_appointments(df)
                    st.success("Appointment cancelled")
            elif action == "Reschedule":
                new_date = st.date_input("New Date", datetime.today())
                new_time = st.time_input("New Time")
                if st.button("🔄 Reschedule"):
                    df.at[selected_idx, "AppointmentDate"] = new_date.strftime("%Y-%m-%d")
                    df.at[selected_idx, "AppointmentTime"] = new_time.strftime("%H:%M")
                    df.at[selected_idx, "Status"] = "Rescheduled"
                    save_appointments(df)
                    st.success("Appointment rescheduled")

# ----------------- Calendar -----------------
st.subheader("📅 Calendar")

df = load_appointments()
if selected_doctor:
    df = df[df["Doctor"] == selected_doctor]

if not df.empty:
    doctor_colors = {"Dr. Ankur Poddar": "#3b82f6"}
    events = []
    for _, row in df.iterrows():
        if row["Status"] != "Cancelled":
            events.append({
                "title": f"{row['Name']} ({row['Doctor']})",
                "start": f"{row['AppointmentDate']}T{row['AppointmentTime']}:00",
                "color": doctor_colors.get(str(row["Doctor"]), "#10b981")
            })

    calendar_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
      <script>
        document.addEventListener('DOMContentLoaded', function() {
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            height: 600,
            headerToolbar: {
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: EVENTS_PLACEHOLDER
          });
          calendar.render();
        });
      </script>
    </head>
    <body>
      <div id='calendar'></div>
    </body>
    </html>
    """.replace("EVENTS_PLACEHOLDER", json.dumps(events))

    components.html(calendar_html, height=650, scrolling=True)

# ----------------- Today & Export -----------------
st.subheader("📋 Today’s Appointments")
df = load_appointments()
if selected_doctor:
    df = df[df["Doctor"] == selected_doctor]

if not df.empty:
    today = datetime.today().strftime("%Y-%m-%d")
    todays = df[(df["AppointmentDate"] == today) & (df["Status"] != "Cancelled")]
    if not todays.empty:
        st.dataframe(todays, use_container_width=True)
    else:
        st.info("No appointments today.")

    if role == "Reception/Staff":
        with open(APPOINTMENT_FILE, "rb") as f:
            st.download_button("📥 Download appointments.xlsx", data=f, file_name="appointments.xlsx")
