import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="📅", layout="wide")

APPOINTMENT_FILE = "appointments.xlsx"

st.title("🏥 Buddha Clinic - Appointment Booking")

# ====== Appointment Form ======
st.subheader("📌 Book a New Appointment")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

with col2:
    mobile = st.text_input("Mobile Number")
    appt_date = st.date_input("Appointment Date", datetime.today())
    appt_time = st.time_input("Appointment Time")
    doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

if st.button("✅ Book Appointment"):
    if name and mobile:
        new_entry = pd.DataFrame([{
            "Name": name,
            "Age": age,
            "Gender": gender,
            "Mobile": mobile,
            "AppointmentDate": appt_date.strftime("%Y-%m-%d"),
            "AppointmentTime": appt_time.strftime("%H:%M"),
            "Doctor": doctor,
            "BookedOn": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])

        if os.path.exists(APPOINTMENT_FILE):
            old = pd.read_excel(APPOINTMENT_FILE)
            df = pd.concat([old, new_entry], ignore_index=True)
        else:
            df = new_entry

        df.to_excel(APPOINTMENT_FILE, index=False)
        st.success(f"✅ Appointment booked for {name} with {doctor} on {appt_date} at {appt_time}")

        # 🔄 Force rerun so calendar refreshes
        st.experimental_rerun()
    else:
        st.error("⚠️ Please enter at least Patient Name and Mobile Number")

# ====== Calendar View ======
st.subheader("📅 Appointment Calendar")

if os.path.exists(APPOINTMENT_FILE):
    df = pd.read_excel(APPOINTMENT_FILE)

    # Convert to events JSON for FullCalendar
    events = []
    for _, row in df.iterrows():
        events.append({
            "title": f"{row['Name']} ({row['Doctor']})",
            "start": f"{row['AppointmentDate']}T{row['AppointmentTime']}:00",
        })

    # HTML/JS for FullCalendar
    calendar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            headerToolbar: {{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }},
            events: {events}
          }});
          calendar.render();
        }});
      </script>
    </head>
    <body>
      <div id='calendar'></div>
    </body>
    </html>
    """

    # 🔄 Always re-render the component
    components.html(calendar_html, height=650, scrolling=True, key=datetime.now().strftime("%H%M%S"))
else:
    st.info("No appointments booked yet. Book one to see it on the calendar.")
