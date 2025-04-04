import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from datetime import datetime
from urllib.parse import urljoin

class SHLProductEnricher:
    def __init__(self, delay=2):
        """
        Initialize the SHL product enricher to add detailed information from product pages
        
        Args:
            delay (int): Delay between requests in seconds
        """
        self.input_csv = "shl_product_catalog_full.csv"  # Static input file
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.df = None
    
    def load_csv(self):
        """Load the input CSV file into a DataFrame"""
        try:
            self.df = pd.read_csv(self.input_csv)
            print(f"Loaded {len(self.df)} records from {self.input_csv}")
            return True
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return False
    
    def scrape_product_details(self, url):
        """
        Scrape additional details from a product page based on the known HTML structure
        
        Args:
            url (str): URL of the product page
            
        Returns:
            dict: Dictionary with additional product details
        """
        details = {
            'description': '',
            'job_levels': '',
            'languages': '',
            'assessment_length': '',
            'completion_time_minutes': '',
            'full_test_type': ''
        }
        
        try:
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Based on the HTML structure you provided, look for product details
            # in the specific divs with class "product-catalogue-training-calendar_row"
            
            # Find all rows that might contain product information
            calendar_rows = soup.find_all(class_=lambda c: c and "product-catalogue-training-calendar" in c)
            
            for row in calendar_rows:
                # Find the header/title for this section
                header = row.find(['h4', 'h3', 'h2'])
                if not header:
                    continue
                
                header_text = header.text.strip().lower()
                paragraph = row.find('p')
                
                if not paragraph:
                    continue
                    
                content = paragraph.text.strip()
                
                # Extract specific information based on header text
                if 'description' in header_text:
                    details['description'] = content
                
                elif 'job levels' in header_text or 'job level' in header_text:
                    details['job_levels'] = content
                
                elif 'languages' in header_text or 'language' in header_text:
                    details['languages'] = content
                
                elif 'assessment length' in header_text or 'test length' in header_text:
                    details['assessment_length'] = content
                    
                    # Try to extract completion time in minutes
                    time_match = re.search(r'(\d+)\s*minutes|minute', content, re.IGNORECASE)
                    if time_match:
                        details['completion_time_minutes'] = time_match.group(1)
                    else:
                        # Another pattern: "Approximate Completion Time in minutes 49"
                        time_match = re.search(r'Time\s+in\s+minutes\s+(\d+)', content, re.IGNORECASE)
                        if time_match:
                            details['completion_time_minutes'] = time_match.group(1)
            
            # For Test Type, look for the specific structure with span elements
            test_type_elem = soup.find(string=re.compile('Test Type:', re.IGNORECASE))
            if test_type_elem:
                parent_elem = test_type_elem.parent
                if parent_elem:
                    # Get the sibling span that contains the test type info
                    span_elem = parent_elem.find('span', class_=lambda c: c and 'ms-2' in c)
                    if span_elem:
                        details['full_test_type'] = span_elem.text.strip()
                    
                    # Also check for product-catalogue keys which might represent test types
                    keys = parent_elem.find_all('span', class_='product-catalogue_key')
                    if keys:
                        key_texts = [key.text.strip() for key in keys if key.text.strip()]
                        if key_texts:
                            # If we already have a test type but it doesn't have these keys, append them
                            if details['full_test_type'] and not all(key in details['full_test_type'] for key in key_texts):
                                details['full_test_type'] += f" ({', '.join(key_texts)})"
                            elif not details['full_test_type']:
                                details['full_test_type'] = ', '.join(key_texts)
            
            # If we couldn't find test type with the above method, try another approach
            if not details['full_test_type']:
                test_type_div = soup.find('div', class_=lambda c: c and 'd-flex' in c and 'flex' in c)
                if test_type_div:
                    test_type_text = test_type_div.text.strip()
                    if 'Test Type:' in test_type_text:
                        # Extract everything after "Test Type:"
                        match = re.search(r'Test Type:\s*(.*?)(?:Remote Testing:|$)', test_type_text, re.IGNORECASE | re.DOTALL)
                        if match:
                            details['full_test_type'] = match.group(1).strip()
            
            # If we still don't have a description, try a more general approach
            if not details['description']:
                # Find any section that might contain a description
                main_content = soup.find('div', class_=lambda c: c and 'col-12' in c and 'col-md-8' in c)
                if main_content:
                    # Look for the first paragraph that's not part of another identified section
                    first_para = main_content.find('p')
                    if first_para and first_para.text.strip():
                        details['description'] = first_para.text.strip()
            
            return details
            
        except Exception as e:
            print(f"Error scraping product details: {e}")
            return details
    
    def enrich_catalog(self, output_dir="./output"):
        """
        Enrich catalog data by scraping product pages
        
        Args:
            output_dir (str): Directory to save output files
            
        Returns:
            pandas.DataFrame: Enriched DataFrame
        """
        if self.df is None:
            if not self.load_csv():
                return None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Add new columns
        self.df['description'] = ''
        self.df['job_levels'] = ''
        self.df['languages'] = ''
        self.df['assessment_length'] = ''
        self.df['completion_time_minutes'] = ''
        self.df['full_test_type'] = ''
        
        # Process each URL
        for i, row in self.df.iterrows():
            if i > 0 and i % 5 == 0:
                print(f"Progress: {i}/{len(self.df)} products processed")
            
            url = row['product_url']
            if not url or pd.isna(url):
                print(f"Skipping row {i}: No URL found")
                continue
                
            # Make sure URL is absolute
            if not url.startswith('http'):
                url = urljoin('https://www.shl.com', url)
            
            # Scrape details
            details = self.scrape_product_details(url)
            
            # Update DataFrame
            for key, value in details.items():
                self.df.at[i, key] = value
            
            # Delay before next request
            if i < len(self.df) - 1:
                print(f"Waiting {self.delay} seconds before next request...")
                time.sleep(self.delay)
        
        return self.df
    
    def save_enriched_data(self, output_dir="./output"):
        """
        Save the enriched data to a CSV file
        
        Args:
            output_dir (str): Directory to save output file
            
        Returns:
            str: Path to the saved file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f'final_shl_{timestamp}.csv')
        
        try:
            self.df.to_csv(filename, index=False)
            print(f"\nSaved enriched data to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None

def main():
    """
    Main function to run the enricher with static input file
    """
    # Set default parameters
    delay = 3
    output_dir = './output'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create an enricher instance with static input file
    enricher = SHLProductEnricher(delay=delay)
    
    # Run the enricher
    start_time = time.time()
    print(f"Starting enrichment process with static input file: shl_product_catalog_full.csv")
    enriched_df = enricher.enrich_catalog(output_dir=output_dir)
    end_time = time.time()
    
    if enriched_df is not None and not enriched_df.empty:
        # Save results to CSV
        output_file = enricher.save_enriched_data(output_dir=output_dir)
        
        # Display the first few rows
        print("\nPreview of enriched data:")
        print(enriched_df.head())
        
        # Print statistics
        print(f"\nTotal products enriched: {len(enriched_df)}")
        print(f"New columns added: description, job_levels, languages, assessment_length, completion_time_minutes, full_test_type")
        
        # Print execution time
        execution_time = end_time - start_time
        print(f"\nTotal execution time: {execution_time:.2f} seconds")
    else:
        print("No data enriched. Please check the input CSV file.")

# Run the script
if __name__ == "__main__":
    main()