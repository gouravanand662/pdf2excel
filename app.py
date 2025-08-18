import streamlit as st
import pdfplumber
import re
import io
import pandas as pd

st.set_page_config(page_title="AI PDF to Excel", layout="centered")
st.title("PDF Bank Statement → Excel Converter")
st.write("Upload your bank statement PDF and convert it to Excel automatically (Text-based only).")

uploaded_file = st.file_uploader("📂 Upload PDF", type="pdf")

# --- Transaction Parser ---
def parse_transactions(text):
    transactions = []
    # Flexible regex for multiple date formats and amounts
    pattern = r"(\d{1,2}[-/ ]?[A-Za-z]{3}[-/ ]?\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(.+?)\s+([-+]?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)"
    matches = re.findall(pattern, text)

    for match in matches:
        date, desc, amount = match
        amount = float(amount.replace(",", ""))
        credit = amount if amount > 0 else 0
        debit = -amount if amount < 0 else 0
        transactions.append({
            "Date": date.strip(),
            "Description": desc.strip(),
            "Amount": amount,
            "Credit": credit,
            "Debit": debit
        })
    return transactions


if uploaded_file is not None:
    st.success("✅ PDF uploaded successfully!")

    # Extract text with pdfplumber
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    if full_text.strip() == "":
        st.error("❌ No text detected. Maybe this is a scanned PDF? Try OCR version.")
    else:
        st.text_area("📄 Raw Extracted Text", full_text, height=200)

        # Parse with regex
        transactions = parse_transactions(full_text)

        if transactions:
            final_df = pd.DataFrame(transactions)
            st.success(f"✅ Extracted {len(final_df)} transactions!")

            # Show extracted transactions
            st.dataframe(final_df)

            # Download Excel
            excel_buffer = io.BytesIO()
            final_df.to_excel(excel_buffer, index=False)
            st.download_button(
                label="📥 Download Excel",
                data=excel_buffer,
                file_name="transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ Could not parse transactions. Please check the raw text above.")
