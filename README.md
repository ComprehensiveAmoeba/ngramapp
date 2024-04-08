# n-gram Analysis from SP Search Term Report

## Overview
The n-gram Analysis from SP Search Term Report is a Streamlit app designed for analyzing Amazon Sponsored Products (SP) search term reports. It facilitates the extraction of meaningful n-gram data to optimize Amazon PPC campaigns, focusing on customer search terms and their performance metrics. This tool supports advertisers in making data-driven decisions to enhance the visibility and performance of their Amazon listings.

## Features
- **Branded Term Exclusion**: Allows users to exclude specific branded terms from the analysis to focus on generic search terms.
- **n-gram Aggregation**: Aggregates data into monograms, bigrams, and trigrams for comprehensive analysis.
- **Performance Metrics Calculation**: Calculates key metrics such as Click-Through Rate (CTR), Conversion Rate, ACOS (Advertising Cost of Sale), CPA (Cost Per Acquisition), and CPC (Cost Per Click) for each n-gram.
- **Excel Output**: Generates an Excel report with aggregated data and performance metrics, sorted by Spend.

## How to Use
1. **Prepare the SP Search Term Report**: Download the "60 days SP ST report" from Amazon's Bulk Uploads section in the Ad Console.
2. **Access the App**: Open the [n-gram Analysis Streamlit app](https://ngramapp.streamlit.app/) in your web browser.
3. **Upload the Report**: Use the file uploader to select and upload your SP Search Term Report in `.xlsx` format.
4. **Enter ASINs and Branded Terms**: Input the ASINs you wish to analyze, one per line, and optionally enter any branded terms you want to exclude from the analysis, also one per line.
5. **Run the Analysis**: Click the "Perform n-gram analysis" button to process your report.
6. **Download the Results**: Upon completion, a link to download the Excel file with the analysis results will be provided. The file is named with a timestamp to indicate the creation time.

## Input Details
- **SP Search Term Report**: Ensure the report is in `.xlsx` format and contains the necessary columns for analysis.
- **ASINs**: List the ASINs you're targeting with your campaigns, separated by newlines.
- **Branded Terms**: Optionally list any branded terms you wish to exclude, separated by newlines.

## Output Format
The output Excel file contains four tabs:
- **Monograms**: Analysis of single-word search terms.
- **Bigrams**: Analysis of two-word search terms.
- **Trigrams**: Analysis of three-word search terms.
- **Report**: A combined report tab with all n-grams analyzed, their metrics, and associated campaign IDs.

## Dependencies
- Streamlit
- Pandas
- NLTK
- Openpyxl

## App Code Structure
- `clean_tokenize`: Tokenizes and cleans the customer search terms from the uploaded report.
- `aggregate_ngrams`: Performs n-gram aggregation and metrics calculation.
- `Streamlit App Layout`: Defines the interactive user interface and data processing workflow.

## Troubleshooting
- **Upload Errors**: Ensure the file is in the correct `.xlsx` format and not corrupted.
- **Missing Data**: Check if the ASINs are correctly listed and the search term report includes all required columns.
- **Analysis Errors**: Verify that the branded terms (if any) are correctly inputted to avoid excluding relevant data inadvertently.

## Support
For support or to report any issues, please contact ComprehensiveAmoeba ;) 

