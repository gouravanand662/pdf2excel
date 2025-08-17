import streamlit as st
import pdfplumber
import camelot
import pytesseract
from PIL import Image
import io
import openai
import json
import pandas as pd

st.set_page_config(page_title="AI PDF to Excel", layout="centered")
st.title("AI-Powered PDF to Excel Converter")
st.write("Upload your bank statement PDF and convert it to Excel automatically.")

# Add your OpenAI API key here or set as environment variable
openai.api_key = st.secrets.get("OPENAI_API_KEY") # or "YOUR_OPENAI_API_KEY"

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    st.success("PDF uploaded successfully!")

    method = st.radio("Choose Extraction Method:", ["Table-based", "Text-based AI"])

    final_df = pd.DataFrame()

    if method == "Table-based":
        # Table extraction using Camelot
        tables = camelot.read_pdf(uploaded_file, pages='all', flavor='stream')
        if tables:
            dfs = [table.df for table in tables]
            final_df = pd.concat(dfs, ignore_index=True)
            st.success(f"Extracted {len(final_df)} rows from tables!")
        else:
            st.warning("No tables detected. Try Text-based AI method.")

    else:
        # Text-based AI parsing
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        if full_text.strip() == "":
            st.error("No text detected. Maybe a scanned PDF? Try Table-based or OCR method.")
        else:
            st.info("Parsing transactions using AI...")
            prompt = f"""
            Extract all bank transactions from the following text.
            Each transaction must have Date (YYYY-MM-DD), Description, Amount, Credit, Debit.
            Return ONLY a JSON array. Example:
            [
              {{"Date":"2025-08-15","Description":"ATM Withdrawal","Amount":500,"Credit":0,"Debit":500}}
            ]
            Text:
            {full_text}
            """

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0
                )
                ai_output = response['choices'][0]['message']['content']
                data = json.loads(ai_output)
                final_df = pd.DataFrame(data)
                st.success(f"AI extracted {len(final_df)} transactions!")
            except Exception as e:
                st.error(f"AI could not parse the PDF. Error: {e}")

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
      
