import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
import pytz

# ========== CONFIG ==========
st.set_page_config(page_title="Buddha Clinic - Appointments", page_icon="🏥", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
APPOINTMENT_FILE = "appointments.xlsx"

# ========== HELPERS ==========
def valid_mobile(m: str) -> bool:
    m = m.strip().replace(" ", "").replace("-", "")
    return m.isdigit() and (len(m) in (10, 12))

def wa_link(number: str, text: str) -> str:
    num = number.strip().replace(" ", "").replace("-", "")
    if len(num) == 10:
        num = "91" + num
    return f"https://wa.me/{num}?text={urllib.parse.quote(text)}"

def load_appointments() -> pd.DataFrame:
    cols = [
        "ID","PatientID","Name","Age","Gender","Height","Weight","Mobile",
        "AppointmentDate","AppointmentTime","Doctor","Notes","Status",
        "BookedOn","ReportFiles","PrescriptionFiles","FollowUpDate","Diagnosis"
    ]
    if os.path.exists(APPOINTMENT_FILE):
        df = pd.read_excel(APPOINTMENT_FILE)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df[cols]
    return pd.DataFrame(columns=cols)

def save_appointments(df: pd.DataFrame):
    df.to_excel(APPOINTMENT_FILE, index=False)

def generate_ids(df: pd.DataFrame):
    if "ID" not in df.columns or df["ID"].dropna().empty:
        new_id = 1
    else:
        new_id = int(df["ID"].dropna().max()) + 1
    patient_id = f"P{str(new_id).zfill(4)}"
    return new_id, patient_id

# ========== ROLE SELECT ==========
st.title("🏥 Buddha Clinic - Appointment System")
role = st.radio("👥 Select Role", ["Patient", "Reception/Staff", "Doctor"])

# ---------- Passwords ----------
if role == "Reception/Staff":
    pw = st.text_input("Enter Staff Password", type="password")
    if pw != "staff123":
        st.warning("🔒 Enter valid Staff password to continue")
        st.stop()

if role == "Doctor":
    pw = st.text_input("Enter Doctor Password", type="password")
    if pw != "doctor123":
        st.warning("🔒 Enter valid Doctor password to continue")
        st.stop()

# =======================================================
# 📌 PATIENT BOOKING
# =======================================================
if role == "Patient":
    st.subheader("📌 Book a New Appointment")

    name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.text_input("Height (cm)")
    weight = st.text_input("Weight (kg)")
    mobile = st.text_input("Mobile Number")
    appt_date = st.date_input("Appointment Date", datetime.now(IST).date())
    appt_time = st.time_input("Appointment Time")
    doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])
    notes = st.text_area("Notes / Reason for Visit")

    if st.button("✅ Book Appointment"):
        if not name or not mobile:
            st.error("⚠️ Name and Mobile required")
        elif not valid_mobile(mobile):
            st.error("⚠️ Invalid mobile number")
        else:
            df = load_appointments()
            appt_id, patient_id = generate_ids(df)

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
                "FollowUpDate": "",
                "Diagnosis": ""
            }])

            df = pd.concat([df, new_entry], ignore_index=True)
            save_appointments(df)

            st.success(f"✅ Appointment booked for {name} with {doctor} on {appt_date} at {appt_time}")
            msg = f"Hello {name}, your appointment with {doctor} is confirmed on {appt_date} at {appt_time}. - Buddha Clinic"
            st.markdown(f"[📲 Send WhatsApp Confirmation]({wa_link(mobile, msg)})", unsafe_allow_html=True)

# =======================================================
# 📌 RECEPTION / STAFF SECTION
# =======================================================
if role == "Reception/Staff":
    st.subheader("📌 Book a New Appointment")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        height = st.text_input("Height (cm)")
        weight = st.text_input("Weight (kg)")
        notes = st.text_area("Notes / Reason for Visit")
    with col2:
        mobile = st.text_input("Mobile Number")
        appt_date = st.date_input("Appointment Date", datetime.now(IST).date())
        appt_time = st.time_input("Appointment Time")
        doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

    if st.button("✅ Book Appointment (Staff)"):
        if not name or not mobile:
            st.error("⚠️ Name and Mobile required")
        elif not valid_mobile(mobile):
            st.error("⚠️ Invalid mobile number")
        else:
            df = load_appointments()
            appt_id, patient_id = generate_ids(df)

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
                "FollowUpDate": "",
                "Diagnosis": ""
            }])

            df = pd.concat([df, new_entry], ignore_index=True)
            save_appointments(df)
            st.success(f"✅ Appointment booked for {name} with {doctor} on {appt_date} at {appt_time}")

    # ---- Upload Reports ----
    st.subheader("📎 Upload Patient Report")
    df = load_appointments()
    if not df.empty:
        patient_choice = st.selectbox("Select Patient", df["Name"].astype(str) + " (" + df["PatientID"].astype(str) + ")")
        if patient_choice:
            pid = patient_choice.split("(")[-1].replace(")", "")
            uploaded_report = st.file_uploader("Upload Report", type=["pdf","jpg","jpeg","png"])
            if uploaded_report:
                reports_dir = "reports"
                os.makedirs(reports_dir, exist_ok=True)
                filename = f"{reports_dir}/{pid}_{datetime.now(IST).strftime('%Y%m%d_%H%M')}_{uploaded_report.name}"
                with open(filename, "wb") as f:
                    f.write(uploaded_report.getbuffer())
                current_reports = df.loc[df["PatientID"] == pid, "ReportFiles"].values[0]
                new_reports = (str(current_reports) + ";" + filename).strip(";") if current_reports else filename
                df.loc[df["PatientID"] == pid, "ReportFiles"] = new_reports
                save_appointments(df)
                st.success("✅ Report uploaded")

    # ---- Delete Appointment ----
    st.subheader("🗑 Delete Appointment")
    df = load_appointments()
    if not df.empty:
        del_choice = st.selectbox("Select Appointment to Delete", df["ID"].astype(str) + " - " + df["Name"])
        if del_choice:
            del_id = int(del_choice.split(" - ")[0])
            if st.button("⚠️ Confirm Delete"):
                df = df[df["ID"] != del_id]
                save_appointments(df)
                st.success("✅ Appointment deleted")

# =======================================================
# 👨‍⚕️ DOCTOR SECTION
# =======================================================
if role == "Doctor":
    st.subheader("👨‍⚕️ Doctor Dashboard")
    df = load_appointments()

    if not df.empty:
        selected = st.selectbox("Select appointment", df["ID"].astype(str) + " - " + df["Name"])
        if selected:
            appt_id = int(selected.split(" - ")[0])
            appt = df[df["ID"] == appt_id].iloc[0]

            st.write(f"**Patient:** {appt['Name']} (ID: {appt['PatientID']}) | Age: {appt['Age']} | Gender: {appt['Gender']}")
            st.write(f"Height: {appt['Height']} cm | Weight: {appt['Weight']} kg")
            st.write(f"Doctor: {appt['Doctor']} | Date: {appt['AppointmentDate']} {appt['AppointmentTime']}")

            diagnosis = st.text_area("Diagnosis")
            medicines = st.text_area("Medicines (one per line)")
            followup_date = st.date_input("Follow-up Date", datetime.now(IST).date())
            doctor_notes = st.text_area("Doctor Notes")

            if st.button("💊 Save Prescription & Mark Seen"):
                df.loc[df["ID"] == appt_id, "Diagnosis"] = diagnosis
                df.loc[df["ID"] == appt_id, "Status"] = "Seen"
                df.loc[df["ID"] == appt_id, "FollowUpDate"] = followup_date.strftime("%Y-%m-%d")

                pres_dir = "prescriptions"
                os.makedirs(pres_dir, exist_ok=True)
                pres_file = f"{pres_dir}/{appt['PatientID']}_{datetime.now(IST).strftime('%Y%m%d_%H%M')}_prescription.txt"
                with open(pres_file, "w") as f:
                    f.write(f"Patient: {appt['Name']} (ID: {appt['PatientID']})\n")
                    f.write(f"Age: {appt['Age']} | Gender: {appt['Gender']}\n")
                    f.write(f"Height: {appt['Height']} cm | Weight: {appt['Weight']} kg\n")
                    f.write(f"Doctor: {appt['Doctor']}\n")
                    f.write(f"Date: {datetime.now(IST).strftime('%Y-%m-%d %H:%M')}\n\n")
                    f.write(f"Diagnosis:\n{diagnosis}\n\n")
                    f.write("Medicines:\n" + medicines.replace("\n","; ") + "\n\n")
                    f.write(f"Doctor Notes:\n{doctor_notes}\n")

                current_pres = df.loc[df["ID"] == appt_id, "PrescriptionFiles"].values[0]
                new_pres = (str(current_pres) + ";" + pres_file).strip(";") if current_pres else pres_file
                df.loc[df["ID"] == appt_id, "PrescriptionFiles"] = new_pres
                save_appointments(df)
                st.success("✅ Prescription saved")

            # ---- Patient History ----
            st.subheader("📖 Patient History")
            history = df[df["PatientID"] == appt["PatientID"]]
            if not history.empty:
                show_cols = [c for c in ["AppointmentDate","AppointmentTime","Status","Diagnosis","FollowUpDate","PrescriptionFiles","ReportFiles"] if c in history.columns]
                st.dataframe(history[show_cols], use_container_width=True)
            else:
                st.info("No past history found for this patient.")
