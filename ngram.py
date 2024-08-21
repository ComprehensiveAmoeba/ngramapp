import streamlit as st
import pandas as pd
import re
import datetime
from nltk import bigrams, trigrams, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import base64
import shutil
from io import BytesIO

# Streamlit app title and logo
st.title("n-gram analysis tool")

# Explicitly download punkt
nltk.download('punkt', quiet=False)

# Download required nltk resources
nltk.download("wordnet")
nltk.download("stopwords")

# Path to the nltk_data directory
nltk_data_path = nltk.data.find('tokenizers/punkt').path.split('tokenizers')[0]

# Remove nltk_data directory (this will be automatically re-downloaded)
shutil.rmtree(nltk_data_path)

# Re-download the punkt data
nltk.download('punkt', quiet=False)

# Define tokenize and clean text function
def clean_tokenize(text, stop_words=set()):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())
    cleaned_tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    return cleaned_tokens

# Define function to aggregate data for n-grams, including metrics calculation
def aggregate_ngrams(data, ngram_func, stop_words, include_campaign_id=False):
    data["ngrams"] = data["Customer Search Term"].apply(lambda x: list(ngram_func(clean_tokenize(x, stop_words))))
    ngrams_expanded = data.explode("ngrams")
    if not ngrams_expanded.empty:
        aggregated = ngrams_expanded.groupby("ngrams")[["Impressions", "Clicks", "Spend", "Sales", "Units"]].sum().reset_index()
        aggregated["CTR"] = aggregated["Clicks"] / aggregated["Impressions"]
        aggregated["Conversion Rate"] = aggregated["Units"] / aggregated["Clicks"]
        aggregated["ACOS"] = aggregated["Spend"] / aggregated["Sales"]
        aggregated["CPA"] = aggregated["Spend"] / aggregated["Units"]
        aggregated["CPC"] = aggregated["Spend"] / aggregated["Clicks"]

        if include_campaign_id:
            campaign_ids = ngrams_expanded.groupby("ngrams")["Campaign ID"].apply(
                lambda x: ",".join(set(map(str, x)))
            ).reset_index()
            aggregated = pd.merge(aggregated, campaign_ids, on="ngrams", how="left")
        
        return aggregated.sort_values(by="Spend", ascending=False)
    else:
        return pd.DataFrame()

# Load nltk resources and set up stop words
stop_words = set(stopwords.words("english"))
additional_stops = {"in", "for", "the", "of", "if", "when", "and", "de", "para"}
stop_words.update(additional_stops)

# Create tabs for "Bulk Sheet ST Report" and "PBI Report"
tab1, tab2 = st.tabs(["Bulk Sheet ST Report", "PBI Report"])

# Bulk Sheet ST Report tab
with tab1:
    # Streamlit user input for file upload, ASINs, and branded terms
    uploaded_file = st.file_uploader("Upload the 60 days SP ST report from Bulk Uploads in the Ad Console", type="xlsx", key="bulk_upload")
    asin_input = st.text_area("Enter ASIN(s) for which to aggregate the data (one per line)", key="bulk_asin_input")
    branded_terms_input = st.text_area("Optionally enter the branded terms to exclude from the n-gram analysis (one per line)", key="bulk_branded_terms_input")

    # Button to perform n-gram analysis
    if st.button("Perform n-gram analysis - Bulk Sheet ST Report", key="bulk_analyze_button"):
        if uploaded_file is not None and asin_input:
            asins = asin_input.upper().split("\n")
            branded_terms = [term.strip().lower() for term in branded_terms_input.split("\n")]

            df = pd.read_excel(uploaded_file, sheet_name="SP Search Term Report")
            pattern = re.compile(r"B0[A-Z0-9]{8}", re.IGNORECASE)
            df["ASIN"] = df["Campaign Name (Informational only)"].apply(
                lambda x: pattern.search(x).group(0) if pattern.search(x) else None
            )
            df_filtered = df[~df["Customer Search Term"].str.lower().apply(
                lambda x: any(brand in x for brand in branded_terms)
            )]
            df_filtered = df_filtered[df_filtered["ASIN"].isin(asins)]

            monograms_aggregated = aggregate_ngrams(df_filtered, lambda x: x, stop_words, include_campaign_id=True)
            bigrams_aggregated = aggregate_ngrams(df_filtered, bigrams, stop_words, include_campaign_id=True)
            trigrams_aggregated = aggregate_ngrams(df_filtered, trigrams, stop_words, include_campaign_id=True)

            report_df = pd.concat([monograms_aggregated, bigrams_aggregated, trigrams_aggregated], keys=["Monograms", "Bigrams", "Trigrams"])
            report_df.reset_index(level=0, inplace=True)
            report_df.rename(columns={"level_0": "N-Gram Type"}, inplace=True)

            # Save results to a BytesIO buffer
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                monograms_aggregated.to_excel(writer, sheet_name="Monograms", index=False)
                bigrams_aggregated.to_excel(writer, sheet_name="Bigrams", index=False)
                trigrams_aggregated.to_excel(writer, sheet_name="Trigrams", index=False)
                report_df.to_excel(writer, sheet_name="Report", index=False)

            # Generate a timestamp for the filename
            timestamp = datetime.datetime.now().strftime("%Y-%m-%S_%H-%M-%S")
            filename = f"ngram_analysis_output_with_report_{timestamp}.xlsx"

            # Create a link to download the Excel file
            st.success("Analysis completed. Download the report below:")
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please upload a file and enter at least one ASIN.")

# PBI Report tab
with tab2:
        # Pre-upload message with a hyperlink to the PBI Report
    st.markdown(
        'Please download a filtered table from this PBI Report '
        '[here](https://app.powerbi.com/groups/me/reports/204aa7cf-a0c6-4d55-bf10-83a25244e14f/ReportSection?experience=power-bi&clientSideAuth=0)',
        unsafe_allow_html=True
    )
    
    # Streamlit user input for file upload, ASINs, and branded terms
    uploaded_file = st.file_uploader("Upload the PBI Report", type="xlsx", key="pbi_upload")
    asin_input = st.text_area("Enter ASIN(s) for which to aggregate the data (one per line)", key="pbi_asin_input")
    branded_terms_input = st.text_area("Optionally enter the branded terms to exclude from the n-gram analysis (one per line)", key="pbi_branded_terms_input")

    # Button to perform n-gram analysis
    if st.button("Perform n-gram analysis - PBI Report", key="pbi_analyze_button"):
        if uploaded_file is not None and asin_input:
            asins = asin_input.upper().split("\n")
            branded_terms = [term.strip().lower() for term in branded_terms_input.split("\n")]

            # Read the Excel file without specifying the sheet name
            df = pd.read_excel(uploaded_file)
            
            # Check and handle NaN or non-string values in the "Customer Search Term"
            df["Customer Search Term"] = df["Customer Search Term"].astype(str)  # Ensure all values are strings
            
            # Filter out branded terms
            df_filtered = df[~df["Customer Search Term"].str.lower().apply(
                lambda x: any(brand in x for brand in branded_terms)
            )]

            # Filter for ASINs
            df_filtered = df_filtered[df_filtered["ASIN"].isin(asins)]

            monograms_aggregated = aggregate_ngrams(df_filtered, lambda x: x, stop_words, include_campaign_id=False)
            bigrams_aggregated = aggregate_ngrams(df_filtered, bigrams, stop_words, include_campaign_id=False)
            trigrams_aggregated = aggregate_ngrams(df_filtered, trigrams, stop_words, include_campaign_id=False)

            report_df = pd.concat([monograms_aggregated, bigrams_aggregated, trigrams_aggregated], keys=["Monograms", "Bigrams", "Trigrams"])
            report_df.reset_index(level=0, inplace=True)
            report_df.rename(columns={"level_0": "N-Gram Type"}, inplace=True)

            # Save results to a BytesIO buffer
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                monograms_aggregated.to_excel(writer, sheet_name="Monograms", index=False)
                bigrams_aggregated.to_excel(writer, sheet_name="Bigrams", index=False)
                trigrams_aggregated.to_excel(writer, sheet_name="Trigrams", index=False)
                report_df.to_excel(writer, sheet_name="Report", index=False)

            # Generate a timestamp for the filename
            timestamp = datetime.datetime.now().strftime("%Y-%m-%S_%H-%M-%S")
            filename = f"ngram_analysis_output_pbi_report_{timestamp}.xlsx"

            # Create a link to download the Excel file
            st.success("Analysis completed. Download the report below:")
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please upload a file and enter at least one ASIN.")


