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

    # ✅ no `key` needed here
    components.html(calendar_html, height=650, scrolling=True)
else:
    st.info("No appointments booked yet. Book one to see it on the calendar.")
