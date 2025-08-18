import streamlit as st
import pdfplumber
import camelot
import pandas as pd
import re
import io

st.set_page_config(page_title="PDF to Excel Converter", layout="centered")
st.title("AI-Powered PDF Bank Statement to Excel Converter (Lightweight)")
st.write("Upload your bank statement PDF and convert it to Excel automatically.")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

def parse_transactions(text):
    transactions = []
    # Regex pattern: Date, Description, Amount
    pattern = r"(\d{2,4}[-/]\d{2}[-/]\d{2,4})\s+([A-Za-z0-9\s,.-]+?)\s+([-+]?\d+(?:\.\d{1,2})?)"
    matches = re.findall(pattern, text)
    for match in matches:
        date, desc, amount = match
        amount = float(amount)
        credit = amount if amount > 0 else 0
        debit = -amount if amount < 0 else 0
        transactions.append({
            "Date": date,
            "Description": desc.strip(),
            "Amount": amount,
            "Credit": credit,
            "Debit": debit
        })
    return transactions

if uploaded_file is not None:
    st.success("✅ PDF uploaded successfully!")

    method = st.radio("Choose Extraction Method:", ["Table-based", "Text-based"])

    final_df = pd.DataFrame()

    if method == "Table-based":
        try:
            tables = camelot.read_pdf(uploaded_file, pages='all', flavor='stream')
            if tables:
                dfs = [table.df for table in tables]
                final_df = pd.concat(dfs, ignore_index=True)
                st.success(f"📊 Extracted {len(final_df)} rows from tables!")
            else:
                st.warning("⚠️ No tables detected. Try Text-based method.")
        except Exception as e:
            st.error(f"❌ Error extracting tables: {e}")

    else:  # Text-based
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

        if full_text.strip() == "":
            st.error("⚠️ No text detected. Maybe a scanned PDF? Try Table-based method.")
        else:
            transactions = parse_transactions(full_text)
            if transactions:
                final_df = pd.DataFrame(transactions)
                st.success(f"📄 Extracted {len(final_df)} transactions!")
            else:
                st.error("❌ Could not parse transactions. Try Table-based method.")

    if not final_df.empty:
        st.dataframe(final_df)

        excel_buffer = io.BytesIO()
        final_df.to_excel(excel_buffer, index=False)

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_buffer,
            file_name="transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
