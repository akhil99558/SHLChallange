# SHL Product Catalog Scraper  

A simple web scraper that extracts product information from the SHL product catalog website.  

## Requirements  

- **Python** 3.7+  
- Required packages:  
  - `requests`  
  - `beautifulsoup4`  
  - `pandas`  
  - `lxml`  

## Installation  

Install required packages:  

```bash
pip install -r requirements.txt
Usage
Run the script in your terminal:

bash
Copy
Edit
python shl_scraper.py
Output
The script will:

Create an output directory if it doesn't exist

Save the results to a CSV file with a timestamp in the filename

Display a preview of the scraped data

Data Extracted
For each product, the script collects:

Product title

Product URL

Remote testing capability (Yes/No)

Adaptive/IRT feature (Yes/No)

Test type

Customization
You can modify these variables in the code:

delay: Time between requests (default: 3 seconds)

max_pages: Maximum number of pages to scrape (default: 20)

Troubleshooting
If the scraper fails:

Check your internet connection

Verify that the SHL website structure hasn't changed

Increase the delay between requests

vbnet
Copy
Edit

This will display as formatted Markdown when rendered. 🚀 Let me know if you need any tweaks!