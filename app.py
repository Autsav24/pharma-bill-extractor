import streamlit as st
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="📅", layout="wide")

APPOINTMENT_FILE = "appointments.xlsx"

st.title("🏥 Buddha Clinic - Appointment Booking")

# ----------------- Helpers -----------------
def valid_mobile(m: str) -> bool:
    m = m.strip().replace(" ", "").replace("-", "")
    return m.isdigit() and (len(m) in (10, 12))

def wa_link(number: str, text: str) -> str:
    num = number.strip().replace(" ", "").replace("-", "")
    if len(num) == 10:  # India 10 digit -> prepend +91
        num = "91" + num
    return f"https://wa.me/{num}?text={urllib.parse.quote(text)}"

def load_appointments() -> pd.DataFrame:
    if os.path.exists(APPOINTMENT_FILE):
        return pd.read_excel(APPOINTMENT_FILE)
    return pd.DataFrame(columns=[
        "Name","Age","Gender","Mobile",
        "AppointmentDate","AppointmentTime","Doctor","BookedOn"
    ])

def save_appointments(df: pd.DataFrame):
    df.to_excel(APPOINTMENT_FILE, index=False)

# ----------------- Form -----------------
st.subheader("📌 Book a New Appointment")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

with col2:
    mobile = st.text_input("Mobile Number (10 digits or with country code)")
    appt_date = st.date_input("Appointment Date", datetime.today())
    appt_time = st.time_input("Appointment Time")
    doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

book = st.button("✅ Book Appointment")

if book:
    if not name or not mobile:
        st.error("⚠️ Please enter at least Patient Name and Mobile Number")
    elif not valid_mobile(mobile):
        st.error("⚠️ Enter a valid mobile (10 digits or include country code, e.g., 91XXXXXXXXXX)")
    else:
        df = load_appointments()

        date_str = appt_date.strftime("%Y-%m-%d")
        time_str = appt_time.strftime("%H:%M")

        dup = df[
            (df["Mobile"].astype(str).str.replace(r"[ -]", "", regex=True) == mobile.strip().replace(" ", "").replace("-", "")) &
            (df["AppointmentDate"] == date_str) &
            (df["AppointmentTime"] == time_str)
        ]
        if not dup.empty:
            st.warning("⚠️ Duplicate booking detected for this patient at the same date & time.")
        else:
            new_entry = pd.DataFrame([{
                "Name": name,
                "Age": age,
                "Gender": gender,
                "Mobile": mobile.strip(),
                "AppointmentDate": date_str,
                "AppointmentTime": time_str,
                "Doctor": doctor,
                "BookedOn": datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            save_appointments(df)

            st.success(f"✅ Appointment booked for {name} with {doctor} on {date_str} at {time_str}")

            # WhatsApp confirmation (prefilled message)
            msg = f"Hello {name}, your appointment with {doctor} is confirmed on {date_str} at {time_str}. - Buddha Clinic"
            st.markdown(f"[📲 Send WhatsApp Confirmation]({wa_link(mobile, msg)})", unsafe_allow_html=True)

# ----------------- Calendar -----------------
st.subheader("📅 Appointment Calendar")

df = load_appointments()
if not df.empty:
    # Colors by doctor
    doctor_colors = {
        "Dr. Ankur Poddar": "#3b82f6",  # blue
    }

    events = []
    for _, row in df.iterrows():
        events.append({
            "title": f"{row['Name']} ({row['Doctor']})",
            "start": f"{row['AppointmentDate']}T{row['AppointmentTime']}:00",
            "color": doctor_colors.get(str(row.get("Doctor", "")), "#10b981")
        })

    # Use placeholder replacement instead of f-string
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
            slotMinTime: '08:00:00',
            slotMaxTime: '20:00:00',
            nowIndicator: true,
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
      <style>
        body { margin:0; padding:0; }
        #calendar { max-width: 1100px; margin: 0 auto; }
      </style>
    </head>
    <body>
      <div id='calendar'></div>
    </body>
    </html>
    """.replace("EVENTS_PLACEHOLDER", json.dumps(events))

    components.html(calendar_html, height=650, scrolling=True)
else:
    st.info("No appointments booked yet. Book one to see it on the calendar.")

# ----------------- Today & Export -----------------
st.subheader("📋 Today’s Appointments")
if not df.empty:
    today = datetime.today().strftime("%Y-%m-%d")
    todays = df[df["AppointmentDate"] == today]
    if not todays.empty:
        st.dataframe(todays, use_container_width=True)
    else:
        st.info("No appointments today.")

    with open(APPOINTMENT_FILE, "rb") as f:
        st.download_button("📥 Download appointments.xlsx", data=f, file_name="appointments.xlsx")
