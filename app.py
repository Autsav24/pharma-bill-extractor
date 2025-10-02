import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="📅", layout="wide")

APPOINTMENT_FILE = "appointments.xlsx"

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
        df = pd.read_excel(APPOINTMENT_FILE)
        required_cols = ["ID","PatientID","Name","Age","Gender","Height","Weight",
                         "Mobile","AppointmentDate","AppointmentTime","Doctor",
                         "Notes","Status","BookedOn"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=["ID","PatientID","Name","Age","Gender","Height","Weight",
                                     "Mobile","AppointmentDate","AppointmentTime","Doctor",
                                     "Notes","Status","BookedOn"])

def save_appointments(df: pd.DataFrame):
    df.to_excel(APPOINTMENT_FILE, index=False)

def generate_appointment_id(df):
    if "ID" not in df.columns or df["ID"].dropna().empty:
        return 1
    else:
        numeric_ids = pd.to_numeric(df["ID"], errors="coerce").dropna()
        if numeric_ids.empty:
            return 1
        return int(numeric_ids.max()) + 1

def generate_patient_id(df):
    if "PatientID" not in df.columns or df["PatientID"].dropna().empty:
        return "P0001"
    else:
        last_id = str(df["PatientID"].dropna().iloc[-1])
        if last_id.startswith("P") and last_id[1:].isdigit():
            num = int(last_id[1:]) + 1
        else:
            num = 1
        return f"P{num:04d}"

def save_prescription_pdf(appt, diagnosis, medicines, doctor_notes):
    filename = f"prescription_{appt['PatientID']}_{appt['ID']}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "Buddha Clinic - Prescription")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Patient: {appt['Name']} (ID: {appt['PatientID']})")
    c.drawString(50, 750, f"Age: {appt['Age']} | Gender: {appt['Gender']}")
    c.drawString(50, 730, f"Height: {appt['Height']} cm | Weight: {appt['Weight']} kg")
    c.drawString(50, 710, f"Doctor: {appt['Doctor']}")
    c.drawString(50, 690, f"Date: {appt['AppointmentDate']} {appt['AppointmentTime']}")

    c.line(50, 675, 500, 675)

    # Diagnosis
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 655, "Diagnosis:")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(50, 640)
    text_obj.textLines(diagnosis if diagnosis else "N/A")
    c.drawText(text_obj)

    # Medicines
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 610, "Medicines:")
    c.setFont("Helvetica", 11)
    med_obj = c.beginText(50, 595)
    if medicines:
        for med in medicines.split("\n"):
            med_obj.textLine(f"- {med}")
    else:
        med_obj.textLine("N/A")
    c.drawText(med_obj)

    # Additional Notes
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 560, "Doctor Notes:")
    c.setFont("Helvetica", 11)
    note_obj = c.beginText(50, 545)
    note_obj.textLines(doctor_notes if doctor_notes else "N/A")
    c.drawText(note_obj)

    c.save()
    return filename

# ----------------- Role -----------------
role = st.radio("👥 Who is using this system?", ["Patient", "Reception/Staff", "Doctor"])

if role == "Doctor":
    selected_doctor = st.selectbox("Select Doctor", ["Dr. Ankur Poddar"])
else:
    selected_doctor = None

# ----------------- Patient Booking -----------------
if role == "Patient":
    st.subheader("📌 Book Your Appointment")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", min_value=0, max_value=250, step=1)
        weight = st.number_input("Weight (kg)", min_value=0, max_value=250, step=1)
    with col2:
        mobile = st.text_input("Mobile Number")
        appt_date = st.date_input("Preferred Date", datetime.today())
        appt_time = st.time_input("Preferred Time")
        doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

    if st.button("✅ Confirm Appointment"):
        df = load_appointments()
        date_str = appt_date.strftime("%Y-%m-%d")
        time_str = appt_time.strftime("%H:%M")

        appt_id = generate_appointment_id(df)
        patient_id = generate_patient_id(df)

        new_entry = pd.DataFrame([{
            "ID": appt_id,
            "PatientID": patient_id,
            "Name": name,
            "Age": age,
            "Gender": gender,
            "Height": height,
            "Weight": weight,
            "Mobile": mobile.strip(),
            "AppointmentDate": date_str,
            "AppointmentTime": time_str,
            "Doctor": doctor,
            "Notes": "",
            "Status": "Booked",
            "BookedOn": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])

        df = pd.concat([df, new_entry], ignore_index=True)
        save_appointments(df)

        st.success(f"✅ Appointment booked for {name} with {doctor} on {date_str} at {time_str}")

        msg = f"Hello {name}, your appointment with {doctor} is confirmed on {date_str} at {time_str}. - Buddha Clinic"
        st.markdown(f"[📲 Send WhatsApp Confirmation]({wa_link(mobile, msg)})", unsafe_allow_html=True)

# ----------------- Reception/Staff -----------------
if role == "Reception/Staff":
    st.subheader("📌 Book a New Appointment (Staff)")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", min_value=0, max_value=250, step=1)
        weight = st.number_input("Weight (kg)", min_value=0, max_value=250, step=1)
        notes = st.text_area("Notes / Reason for Visit")
    with col2:
        mobile = st.text_input("Mobile Number")
        appt_date = st.date_input("Appointment Date", datetime.today())
        appt_time = st.time_input("Appointment Time")
        doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

    if st.button("✅ Book Appointment (Staff)"):
        df = load_appointments()
        date_str = appt_date.strftime("%Y-%m-%d")
        time_str = appt_time.strftime("%H:%M")

        appt_id = generate_appointment_id(df)
        patient_id = generate_patient_id(df)

        new_entry = pd.DataFrame([{
            "ID": appt_id,
            "PatientID": patient_id,
            "Name": name,
            "Age": age,
            "Gender": gender,
            "Height": height,
            "Weight": weight,
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

        st.success(f"✅ Appointment booked for {name} ({patient_id}) with {doctor} on {date_str} at {time_str}")

    # ---- Manage Existing Appointments ----
    st.subheader("🛠 Manage Appointments")
    df = load_appointments()
    if not df.empty:
        search = st.text_input("🔍 Search by name or mobile")
        if search:
            df = df[df["Name"].str.contains(search, case=False) | df["Mobile"].astype(str).str.contains(search)]

        st.dataframe(df, use_container_width=True)

        selected = st.selectbox("Select appointment ID to update", df["ID"].astype(str))
        if selected:
            appt = df[df["ID"].astype(str) == selected].iloc[0]
            st.write("Editing:", appt["Name"], "-", appt["AppointmentDate"], appt["AppointmentTime"])

            action = st.radio("Action", ["Cancel", "Reschedule", "Delete"])
            if action == "Cancel":
                if st.button("❌ Cancel Appointment"):
                    df.loc[df["ID"].astype(str) == selected, "Status"] = "Cancelled"
                    save_appointments(df)
                    st.success("Appointment cancelled")
            elif action == "Reschedule":
                new_date = st.date_input("New Date", datetime.today())
                new_time = st.time_input("New Time")
                if st.button("🔄 Reschedule"):
                    df.loc[df["ID"].astype(str) == selected, "AppointmentDate"] = new_date.strftime("%Y-%m-%d")
                    df.loc[df["ID"].astype(str) == selected, "AppointmentTime"] = new_time.strftime("%H:%M")
                    df.loc[df["ID"].astype(str) == selected, "Status"] = "Rescheduled"
                    save_appointments(df)
                    st.success("Appointment rescheduled")
            elif action == "Delete":
                if st.button("🗑️ Delete Appointment"):
                    df = df[df["ID"].astype(str) != selected]
                    save_appointments(df)
                    st.success("Appointment deleted permanently")
    else:
        st.info("No appointments found.")

# ----------------- Doctor Prescription -----------------
if role == "Doctor":
    st.subheader("📝 Write Prescription")
    today = datetime.today().strftime("%Y-%m-%d")
    df = load_appointments()
    df_today = df[(df["Doctor"] == selected_doctor) &
                  (df["AppointmentDate"] == today) &
                  (df["Status"] == "Booked")]

    if not df_today.empty:
        selected = st.selectbox("Select appointment ID", df_today["ID"].astype(str))
        appt = df_today[df_today["ID"].astype(str) == selected].iloc[0]

        diagnosis = st.text_area("Diagnosis")
        medicines = st.text_area("Medicines (one per line)")
        doctor_notes = st.text_area("Additional Notes")

        if st.button("💊 Save Prescription"):
            pdf_file = save_prescription_pdf(appt, diagnosis, medicines, doctor_notes)
            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download Prescription PDF", f, file_name=pdf_file)
    else:
        st.info("No booked appointments today.")
