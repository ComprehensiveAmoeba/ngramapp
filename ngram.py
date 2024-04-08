import streamlit as st
import pandas as pd
import re
import datetime
from nltk import bigrams, trigrams, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import base64
from io import BytesIO

# Streamlit app title and logo
st.title("n-gram analysis from SP Search Term report")
st.image("https://media.licdn.com/dms/image/C4E0BAQFNgWlJu-JJOQ/company-logo_200_200/0/1639577716977/thrasio_logo?e=1720656000&v=beta&t=WQrshnM1GaRAOzxHmkL893JYFmZ9r6ZfYdkLRRD8_ZM")

# Download required nltk resources
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

# Define tokenize and clean text function
def clean_tokenize(text, stop_words=set()):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())  # Tokenize and lowercase
    cleaned_tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    return cleaned_tokens

# Define function to aggregate data for n-grams, including metrics calculation
def aggregate_ngrams(data, ngram_func, stop_words):
    data['ngrams'] = data['Customer Search Term'].apply(lambda x: list(ngram_func(clean_tokenize(x, stop_words))))
    ngrams_expanded = data.explode('ngrams')
    if not ngrams_expanded.empty:
        aggregated = ngrams_expanded.groupby('ngrams')[['Impressions', 'Clicks', 'Spend', 'Sales', 'Units']].sum().reset_index()
        aggregated['CTR'] = aggregated['Clicks'] / aggregated['Impressions']
        aggregated['Conversion Rate'] = aggregated['Units'] / aggregated['Clicks']
        aggregated['ACOS'] = aggregated['Spend'] / aggregated['Sales']
        aggregated['CPA'] = aggregated['Spend'] / aggregated['Units']
        aggregated['CPC'] = aggregated['Spend'] / aggregated['Clicks']
        campaign_ids = ngrams_expanded.groupby('ngrams')['Campaign ID'].apply(lambda x: ','.join(set(map(str, x)))).reset_index()
        aggregated = pd.merge(aggregated, campaign_ids, on='ngrams', how='left')
        return aggregated.sort_values(by='Spend', ascending=False)
    else:
        return pd.DataFrame()

# Load nltk resources and set up stop words
stop_words = set(stopwords.words('english'))
additional_stops = {'in', 'for', 'the', 'of', 'if', 'when', 'and', 'de', 'para'}
stop_words.update(additional_stops)

# Streamlit user input for file upload, ASINs, and branded terms
uploaded_file = st.file_uploader("Upload the 60 days SP ST report from Bulk Uploads in the Ad Console", type='xlsx')
asin_input = st.text_area("Enter ASIN(s) for which to aggregate the data (one per line)")
branded_terms_input = st.text_area("Optionally enter the branded terms to exclude from the n-gram analysis (one per line)")

# Button to perform n-gram analysis
if st.button('Perform n-gram analysis'):
    if uploaded_file is not None and asin_input:
        asins = asin_input.upper().split('\n')
        branded_terms = [term.strip().lower() for term in branded_terms_input.split('\n')]
        
        df = pd.read_excel(uploaded_file, sheet_name='SP Search Term Report')
        pattern = re.compile(r'B0[A-Z0-9]{8}', re.IGNORECASE)
        df['ASIN'] = df['Campaign Name (Informational only)'].apply(lambda x: pattern.search(x).group(0) if pattern.search(x) else None)
        df_filtered = df[~df['Customer Search Term'].str.lower().apply(lambda x: any(brand in x for brand in branded_terms))]
        df_filtered = df_filtered[df_filtered['ASIN'].isin(asins)]
        
        monograms_aggregated = aggregate_ngrams(df_filtered, lambda x: x, stop_words)
        bigrams_aggregated = aggregate_ngrams(df_filtered, bigrams, stop_words)
        trigrams_aggregated = aggregate_ngrams(df_filtered, trigrams, stop_words)
        
        report_df = pd.concat([monograms_aggregated, bigrams_aggregated, trigrams_aggregated], keys=['Monograms', 'Bigrams', 'Trigrams'])
        report_df.reset_index(level=0, inplace=True)
        report_df.rename(columns={'level_0': 'N-Gram Type'}, inplace=True)

        # Save results to a BytesIO buffer
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            monograms_aggregated.to_excel(writer, sheet_name='Monograms', index=False)
            bigrams_aggregated.to_excel(writer, sheet_name='Bigrams', index=False)
            trigrams_aggregated.to_excel(writer, sheet_name='Trigrams', index=False)
            report_df.to_excel(writer, sheet_name='Report', index=False)
        
        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'ngram_analysis_output_with_report_{timestamp}.xlsx'
        
        # Create a link to download the excel file
        st.success('Analysis completed. Download the report below:')
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("Please upload a file and enter at least one ASIN.")
