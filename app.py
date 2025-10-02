import streamlit as st
import pandas as pd
import easyocr
from PIL import Image
import re
import os
from datetime import datetime

# Initialize EasyOCR reader (English)
reader = easyocr.Reader(['en'])

st.title("📄 Pharma Supplier Bill Extractor - Buddha Clinic")

# -------- Helper Function to Extract Fields ----------
def extract_fields(text):
    # --- Estimate No ---
    estimate = None
    match_est = re.search(r"Estimate\s*No\.?\s*:? ?(\d+)", text, re.IGNORECASE)
    if match_est:
        estimate = match_est.group(1)

    # --- Date ---
    date = None
    match_date = re.search(r"(\d{2}[-/]\d{2}[-/]\d{4})", text)
    if match_date:
        date = match_date.group(1)

    # --- Grand Total ---
    total = None
    match_total = re.search(r"(Grand\s*Total|Total)\s*[:]? ?₹?(\d+\.?\d*)", text, re.IGNORECASE)
    if match_total:
        total = match_total.group(2)

    # --- Buyer Name (dynamic, handwritten or printed) ---
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
        # Load image
        img = Image.open(file)

        # OCR using EasyOCR
        result = reader.readtext(img, detail=0)  # detail=0 = only text strings
        text = "\n".join(result)

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
            # Use first date for filename
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
