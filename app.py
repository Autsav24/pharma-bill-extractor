import streamlit as st
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="📅", layout="wide")

APPOINTMENT_FILE = "appointments.xlsx"
REPORTS_DIR = "reports"
PRESCRIPTIONS_DIR = "prescriptions"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(PRESCRIPTIONS_DIR, exist_ok=True)

# ---------- Indian Timezone ----------
IST = pytz.timezone("Asia/Kolkata")

# ----------------- Helpers -----------------
def load_appointments() -> pd.DataFrame:
    if os.path.exists(APPOINTMENT_FILE):
        return pd.read_excel(APPOINTMENT_FILE)
    return pd.DataFrame(columns=[
        "ID","PatientID","Name","Age","Gender","Height","Weight","Mobile",
        "AppointmentDate","AppointmentTime","Doctor","Notes","Status",
        "BookedOn","ReportFiles","PrescriptionFiles","FollowUpDate"
    ])

def save_appointments(df: pd.DataFrame):
    df.to_excel(APPOINTMENT_FILE, index=False)

def generate_appointment_id(df: pd.DataFrame):
    if "ID" not in df.columns or df.empty:
        return 1
    return int(df["ID"].dropna().max()) + 1

def generate_patient_id(df: pd.DataFrame):
    if "PatientID" not in df.columns or df.empty:
        return "P0001"
    existing = [str(x) for x in df["PatientID"].dropna()]
    nums = [int(x.replace("P","")) for x in existing if x.startswith("P")]
    new_num = max(nums) + 1 if nums else 1
    return f"P{new_num:04d}"

# Prescription PDF
def save_prescription_pdf(appt, diagnosis, medicines, doctor_notes, reports, followup):
    filename = f"{PRESCRIPTIONS_DIR}/prescription_{appt['PatientID']}_{appt['ID']}_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, height-2*cm, "Buddha Clinic")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height-2.7*cm, "Dr. Ankur Poddar, MBBS")
    c.drawString(2*cm, height-3.2*cm, "Contact: +91-9876543210")
    c.line(2*cm, height-3.5*cm, width-2*cm, height-3.5*cm)

    # Patient Info
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, height-4.5*cm, f"Name: {appt['Name']}   Age: {appt['Age']} | Gender: {appt['Gender']}")
    c.drawRightString(width-2*cm, height-4.5*cm, f"Height: {appt['Height']} cm   Weight: {appt['Weight']} kg")
    c.drawString(2*cm, height-5.2*cm, f"Date: {appt['AppointmentDate']} {appt['AppointmentTime']}")

    # Diagnosis
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height-6.5*cm, "Clinical Diagnosis:")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(2*cm, height-7.2*cm)
    text_obj.textLines(diagnosis if diagnosis else "N/A")
    c.drawText(text_obj)

    # Medicines
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height-9*cm, "Prescription (℞):")
    c.setFont("Helvetica", 11)
    med_obj = c.beginText(2.5*cm, height-9.7*cm)
    if medicines:
        for med in medicines.split("\n"):
            med_obj.textLine(f"• {med}")
    else:
        med_obj.textLine("N/A")
    c.drawText(med_obj)

    # Reports
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, 6*cm, "Investigations / Reports:")
    c.setFont("Helvetica", 11)
    rep_obj = c.beginText(2.5*cm, 5.5*cm)
    rep_obj.textLines(reports if reports else "None prescribed")
    c.drawText(rep_obj)

    # Notes
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, 4*cm, "Doctor's Notes:")
    c.setFont("Helvetica", 11)
    note_obj = c.beginText(2.5*cm, 3.5*cm)
    note_obj.textLines(doctor_notes if doctor_notes else "N/A")
    c.drawText(note_obj)

    # Follow-up
    if followup:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, 3*cm, f"Next Appointment / Follow-up: {followup}")

    # Footer
    c.line(2*cm, 2.5*cm, width-2*cm, 2.5*cm)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(2*cm, 2*cm, "This is a computer-generated prescription from Buddha Clinic.")
    c.setFont("Helvetica", 12)
    c.drawRightString(width-2*cm, 2*cm, "Doctor's Signature")

    c.save()
    return filename

# ----------------- Role Selection -----------------
role = st.radio("👥 Who is using this system?", ["Patient", "Reception/Staff", "Doctor"])

if role == "Reception/Staff":
    pw = st.text_input("Enter Staff Password", type="password")
    if pw != "709":
        st.warning("🔒 Enter valid Staff password to continue")
        st.stop()

if role == "Doctor":
    pw = st.text_input("Enter Doctor Password", type="password")
    if pw != "709":
        st.warning("🔒 Enter valid Doctor password to continue")
        st.stop()

# ----------------- Patient Booking -----------------
if role == "Patient":
    st.subheader("📌 Book a New Appointment")

    name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=0, step=1)
    weight = st.number_input("Weight (kg)", min_value=0, step=1)
    mobile = st.text_input("Mobile Number")
    appt_date = st.date_input("Appointment Date", datetime.now(IST))
    appt_time = st.time_input("Appointment Time", datetime.now(IST).time())
    doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])
    notes = st.text_area("Notes / Reason for Visit")

    if st.button("✅ Book Appointment"):
        df = load_appointments()
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
            "AppointmentDate": appt_date.strftime("%Y-%m-%d"),
            "AppointmentTime": appt_time.strftime("%H:%M"),
            "Doctor": doctor,
            "Notes": notes,
            "Status": "Booked",
            "BookedOn": datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
            "ReportFiles": "",
            "PrescriptionFiles": "",
            "FollowUpDate": ""
        }])

        df = pd.concat([df, new_entry], ignore_index=True)
        save_appointments(df)

        st.success(f"✅ Appointment booked for {name} with {doctor} on {appt_date} at {appt_time}")

# ----------------- Reception Management -----------------
if role == "Reception/Staff":
    st.subheader("🛠 Manage Appointments")
    df = load_appointments()

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        selected = st.selectbox("Select appointment to update/delete", df["ID"].astype(str))
        appt = df[df["ID"].astype(str) == selected].iloc[0]

        action = st.radio("Action", ["Cancel", "Reschedule", "Delete"])
        if action == "Cancel" and st.button("❌ Cancel Appointment"):
            df.loc[df["ID"] == appt["ID"], "Status"] = "Cancelled"
            save_appointments(df)
            st.success("Appointment cancelled")
        elif action == "Reschedule":
            new_date = st.date_input("New Date", datetime.now(IST))
            new_time = st.time_input("New Time", datetime.now(IST).time())
            if st.button("🔄 Reschedule"):
                df.loc[df["ID"] == appt["ID"], "AppointmentDate"] = new_date.strftime("%Y-%m-%d")
                df.loc[df["ID"] == appt["ID"], "AppointmentTime"] = new_time.strftime("%H:%M")
                df.loc[df["ID"] == appt["ID"], "Status"] = "Rescheduled"
                save_appointments(df)
                st.success("Appointment rescheduled")
        elif action == "Delete" and st.button("🗑 Delete Appointment"):
            df = df[df["ID"] != appt["ID"]]
            save_appointments(df)
            st.success("Appointment deleted")

# ----------------- Doctor Prescription -----------------
if role == "Doctor":
    st.subheader("📝 Write Prescription")
    today = datetime.now(IST).strftime("%Y-%m-%d")
    df = load_appointments()

    df_today = df[(df["Doctor"] == "Dr. Ankur Poddar") &
                  (df["AppointmentDate"] == today) &
                  (df["Status"].isin(["Booked", "Seen"]))]

    if not df_today.empty:
        st.write("### Today's Patients")
        st.dataframe(df_today[["ID","Name","Age","Gender","AppointmentTime","Status"]], use_container_width=True)

        selected = st.selectbox("Select appointment ID", df_today["ID"].astype(str))
        appt = df_today[df_today["ID"].astype(str) == selected].iloc[0]

        st.write(f"📌 Selected Patient: {appt['Name']} ({appt['Age']} yrs, {appt['Gender']}) | Status: {appt['Status']}")

        diagnosis = st.text_area("Diagnosis")
        medicines = st.text_area("Medicines (one per line)")
        reports = st.text_area("Investigations / Reports (जाँच)")
        doctor_notes = st.text_area("Additional Notes")
        followup = st.date_input("Next Follow-up Date (optional)", datetime.now(IST))

        # Upload report
        uploaded_report = st.file_uploader("📎 Upload Report (PDF/Image)", type=["pdf","jpg","jpeg","png"])
        if uploaded_report:
            report_filename = f"{REPORTS_DIR}/{appt['PatientID']}_{datetime.now(IST).strftime('%Y%m%d_%H%M')}_{uploaded_report.name}"
            with open(report_filename, "wb") as f:
                f.write(uploaded_report.getbuffer())
            existing_reports = str(appt["ReportFiles"]) if pd.notna(appt["ReportFiles"]) else ""
            new_reports = existing_reports + ";" + report_filename if existing_reports else report_filename
            df.loc[df["ID"] == appt["ID"], "ReportFiles"] = new_reports
            save_appointments(df)
            st.success("✅ Report uploaded")

        if st.button("💊 Save Prescription & Mark Seen"):
            pdf_file = save_prescription_pdf(appt, diagnosis, medicines, doctor_notes, reports, followup)

            existing_presc = str(appt["PrescriptionFiles"]) if pd.notna(appt["PrescriptionFiles"]) else ""
            new_presc = existing_presc + ";" + pdf_file if existing_presc else pdf_file
            df.loc[df["ID"] == appt["ID"], "PrescriptionFiles"] = new_presc
            df.loc[df["ID"] == appt["ID"], "Status"] = "Seen"
            df.loc[df["ID"] == appt["ID"], "FollowUpDate"] = followup.strftime("%Y-%m-%d") if followup else ""
            save_appointments(df)

            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download Prescription PDF", f, file_name=os.path.basename(pdf_file))

            st.success(f"✅ Prescription saved for {appt['Name']}. Status updated to Seen.")

        # Show patient history
        st.subheader("📖 Patient History")
        history = df[df["PatientID"] == appt["PatientID"]]
        if not history.empty:
            st.dataframe(history[["AppointmentDate","Diagnosis","PrescriptionFiles","ReportFiles","FollowUpDate"]], use_container_width=True)

