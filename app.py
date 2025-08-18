import streamlit as st
import pdfplumber
import camelot
import pandas as pd
import re
import io
from transformers import pipeline

st.set_page_config(page_title="AI PDF to Excel", layout="centered")
st.title("AI-Powered PDF to Excel Converter (Free Alternative)")
st.write("Upload your bank statement PDF and convert it to Excel automatically. No OpenAI needed!")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

# Load a lightweight Hugging Face model (for text cleanup if needed)
generator = pipeline("text-generation", model="distilgpt2")

def parse_transactions(text):
    """
    Simple regex parser for transactions:
    - Date formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
    - Extract Description + Amount
    """
    transactions = []
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
    st.success("PDF uploaded successfully!")

    method = st.radio("Choose Extraction Method:", ["Table-based", "Text-based (Free AI)"])

    final_df = pd.DataFrame()

    if method == "Table-based":
        try:
            tables = camelot.read_pdf(uploaded_file, pages='all', flavor='stream')
            if tables:
                dfs = [table.df for table in tables]
                final_df = pd.concat(dfs, ignore_index=True)
                st.success(f"Extracted {len(final_df)} rows from tables!")
            else:
                st.warning("No tables detected. Try Text-based method.")
        except Exception as e:
            st.error(f"Error extracting tables: {e}")

    else:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        if full_text.strip() == "":
            st.error("No text detected. Maybe a scanned PDF? Try Table-based method.")
        else:
            st.info("Parsing transactions using regex + HuggingFace model...")

            # First pass: regex extraction
            transactions = parse_transactions(full_text)

            # If too few transactions, try HuggingFace cleanup
            if len(transactions) < 3:
                st.warning("Few transactions detected. Trying HuggingFace model to enhance parsing...")
                generated = generator(full_text[:1000], max_length=500, do_sample=False)[0]["generated_text"]
                transactions = parse_transactions(generated)

            if transactions:
                final_df = pd.DataFrame(transactions)
                st.success(f"Extracted {len(final_df)} transactions!")
            else:
                st.error("Could not parse transactions. Try Table-based method.")

    # Show dataframe and download option
    if not final_df.empty:
        st.dataframe(final_df)

        excel_buffer = io.BytesIO()
        final_df.to_excel(excel_buffer, index=False)
        st.download_button(
            label="Download Excel",
            data=excel_buffer,
            file_name="transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
