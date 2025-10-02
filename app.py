import streamlit as st
import pandas as pd
from paddleocr import PaddleOCR
from PIL import Image
import re
import os
from datetime import datetime

# ✅ Cache OCR so it initializes only once
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang='en')

ocr = load_ocr()

# Sidebar Navigation
st.sidebar.title("🏥 Buddha Clinic")
page = st.sidebar.radio("Select Feature:", ["📄 Bill Extractor", "📅 Appointment Booking"])

# ======================================================
# --------- BILL EXTRACTOR -----------------------------
# ======================================================
if page == "📄 Bill Extractor":
    st.title("📄 Pharma Supplier Bill Extractor")

    # -------- Helper Function to Extract Fields ----------
    def extract_fields(text):
        estimate = None
        match_est = re.search(r"Estimate\s*No\.?\s*:? ?(\d+)", text, re.IGNORECASE)
        if match_est:
            estimate = match_est.group(1)

        date = None
        match_date = re.search(r"(\d{2}[-/]\d{2}[-/]\d{4})", text)
        if match_date:
            date = match_date.group(1)

        total = None
        match_total = re.search(r"(Grand\s*Total|Total)\s*[:]? ?₹?(\d+\.?\d*)", text, re.IGNORECASE)
        if match_total:
            total = match_total.group(2)

        buyer = ""
        for line in text.split("\n"):
            if line.strip() and not any(x in line for x in ["M/s", "Dr.", "Chemist", "Pharma", "Estimate", "Total"]):
                buyer = line.strip()
                break

        return {
            "EstimateNo": estimate or "",
            "Date": date or "",
            "GrandTotal": total or "",
            "BuyerName": buyer
        }

    # -------- File Upload Section ----------
    uploaded_files = st.file_uploader(
        "Upload Bill Images (JPG/PNG)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        results = []

        for file in uploaded_files:
            # Save temporarily
            with open(file.name, "wb") as f:
                f.write(file.getbuffer())

            # OCR using PaddleOCR
            ocr_result = ocr.ocr(file.name, cls=True)
            text_lines = []
            for page in ocr_result:
                for line in page:
                    text_lines.append(line[1][0])
            text = "\n".join(text_lines)

            # Extract fields
            fields = extract_fields(text)
            fields["File"] = file.name
            results.append(fields)

        df = pd.DataFrame(results)

        st.write("✅ Extracted Data (you can edit if needed)")
        edited_df = st.data_editor(df, num_rows="dynamic")

        # -------- Validation Rules ----------
        errors = []
        for i, row in edited_df.iterrows():
            if row["EstimateNo"] and not str(row["EstimateNo"]).isdigit():
                errors.append(f"{row['File']} → Invalid Estimate No")
            if row["Date"] and not re.match(r"\d{2}-\d{2}-\d{4}", str(row["Date"])):
                errors.append(f"{row['File']} → Invalid Date")
            if row["GrandTotal"] and not str(row["GrandTotal"]).replace(".", "").isdigit():
                errors.append(f"{row['File']} → Invalid Grand Total")
            if not row["BuyerName"]:
                errors.append(f"{row['File']} → Buyer Name missing")

        if errors:
            st.warning("⚠️ Some issues found:")
            for e in errors:
                st.write("- " + e)

        # -------- Save to Excel (Append Monthly) ----------
        if st.button("💾 Save to Monthly Excel"):
            if not edited_df.empty:
                date_str = edited_df.iloc[0]["Date"] or datetime.today().strftime("%d-%m-%Y")
                try:
                    dt = datetime.strptime(date_str, "%d-%m-%Y")
                except:
                    dt = datetime.today()

                filename = f"bills_{dt.strftime('%Y_%m')}.xlsx"

                if os.path.exists(filename):
                    old_df = pd.read_excel(filename)
                    final_df = pd.concat([old_df, edited_df], ignore_index=True)
                else:
                    final_df = edited_df

                final_df.to_excel(filename, index=False)

                with open(filename, "rb") as f:
                    st.download_button("📥 Download Updated Excel", f, file_name=filename)

                st.success(f"Data saved and appended to {filename}")

# ======================================================
# --------- APPOINTMENT BOOKING ------------------------
# ======================================================
elif page == "📅 Appointment Booking":
    st.title("📅 Patient Appointment Booking")

    APPOINTMENT_FILE = "appointments.xlsx"

    # --- Appointment Form ---
    with st.form("appointment_form"):
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        mobile = st.text_input("Mobile Number")
        appt_date = st.date_input("Appointment Date", datetime.today())
        appt_time = st.time_input("Appointment Time")
        doctor = st.selectbox("Doctor", ["Dr. Ankur Poddar"])

        submitted = st.form_submit_button("Book Appointment")

        if submitted:
            if name and mobile:
                new_entry = pd.DataFrame([{
                    "Name": name,
                    "Age": age,
                    "Gender": gender,
                    "Mobile": mobile,
                    "AppointmentDate": appt_date.strftime("%d-%m-%Y"),
                    "AppointmentTime": appt_time.strftime("%H:%M"),
                    "Doctor": doctor,
                    "BookedOn": datetime.now().strftime("%d-%m-%Y %H:%M")
                }])

                if os.path.exists(APPOINTMENT_FILE):
                    old = pd.read_excel(APPOINTMENT_FILE)
                    df = pd.concat([old, new_entry], ignore_index=True)
                else:
                    df = new_entry

                df.to_excel(APPOINTMENT_FILE, index=False)
                st.success(f"✅ Appointment booked for {name} with {doctor} on {appt_date} at {appt_time}")
            else:
                st.error("⚠️ Please enter at least Patient Name and Mobile Number")

    # --- Show Today's Appointments ---
    st.write("### 📋 Today's Appointments")
    if os.path.exists(APPOINTMENT_FILE):
        all_appts = pd.read_excel(APPOINTMENT_FILE)
        today = datetime.today().strftime("%d-%m-%Y")
        todays_appts = all_appts[all_appts["AppointmentDate"] == today]
        st.dataframe(todays_appts)
    else:
        st.info("No appointments booked yet.")
