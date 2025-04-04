import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from datetime import datetime

class SHLCatalogScraper:
    def __init__(self, base_url="https://www.shl.com/solutions/products/product-catalog/", delay=2):
        """
        Initialize the SHL product catalog scraper for scraping all pages
        
        Args:
            base_url (str): Base URL for the SHL product catalog
            delay (int): Delay between requests in seconds
        """
        self.base_url = base_url
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_catalog_page(self, start=0, product_type=2):
        """
        Get a catalog page based on the start index and product type
        
        Args:
            start (int): Start index for pagination
            product_type (int): Product type filter
            
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        url = f"{self.base_url}?start={start}&type={product_type}&type={product_type}"
        print(f"Fetching URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Check if we got a valid HTML response
            if 'text/html' not in response.headers.get('Content-Type', ''):
                print(f"Warning: Response is not HTML. Content-Type: {response.headers.get('Content-Type')}")
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error retrieving page: {e}")
            return None
    
    def extract_catalog_items(self, soup):
        """
        Extract catalog items with multiple fallback methods
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of dictionaries with catalog item data
        """
        items = []
        
        # METHOD 1: Try table structure first
        rows = soup.select('table tbody tr')
        if not rows:
            # Fallback: try any tr with data-course-id
            rows = soup.select('tr[data-course-id]')
        
        print(f"Found {len(rows)} product rows")
        
        if rows:
            for row in rows:
                product_data = {}
                
                # Get course ID
                product_data['course_id'] = row.get('data-course-id', '')
                
                # Get product title and URL
                title_elem = row.find('a')
                if title_elem:
                    product_data['title'] = title_elem.text.strip()
                    product_data['product_url'] = title_elem['href']
                    if not product_data['product_url'].startswith('http'):
                        product_data['product_url'] = 'https://www.shl.com' + product_data['product_url']
                
                # Get all td elements
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # Remote Testing (cell 2) - check for circle or yes indicator
                    remote_cell = cells[1]
                    remote_yes = remote_cell.find(class_=lambda c: c and ('yes' in c or 'circle' in c))
                    product_data['remote_testing'] = 'Yes' if remote_yes else 'No'
                    
                    # Adaptive/IRT (cell 3) - check for circle or yes indicator
                    adaptive_cell = cells[2]
                    adaptive_yes = adaptive_cell.find(class_=lambda c: c and ('yes' in c or 'circle' in c))
                    product_data['adaptive_irt'] = 'Yes' if adaptive_yes else 'No'
                    
                    # Test Type (cell 4) - Get all text
                    test_type_cell = cells[3]
                    # Try to get specific keys first
                    keys = test_type_cell.find_all(class_=lambda c: c and 'key' in c)
                    if keys:
                        test_types = [key.text.strip() for key in keys]
                        product_data['test_type'] = ', '.join(filter(None, test_types))
                    else:
                        # Fallback to all text
                        product_data['test_type'] = test_type_cell.text.strip()
                
                items.append(product_data)
        else:
            # METHOD 2: Fallback to looking for product links in any context
            print("Falling back to product link search")
            product_links = soup.find_all('a', href=re.compile('/solutions/products/product-catalog/view/'))
            
            for link in product_links:
                product_data = {}
                product_data['title'] = link.text.strip()
                product_data['product_url'] = link['href']
                if not product_data['product_url'].startswith('http'):
                    product_data['product_url'] = 'https://www.shl.com' + product_data['product_url']
                
                # Try to find parent elements that might contain the other info
                parent = link.find_parent('div') or link.find_parent('tr')
                if parent:
                    # Look for common indicators for Remote Testing and Adaptive/IRT
                    remote_elem = parent.find(string=re.compile('Remote', re.IGNORECASE)) or parent.find(class_=lambda c: c and 'remote' in c.lower())
                    product_data['remote_testing'] = 'Yes' if remote_elem else 'Unknown'
                    
                    adaptive_elem = parent.find(string=re.compile('Adaptive|IRT', re.IGNORECASE)) or parent.find(class_=lambda c: c and ('adaptive' in c.lower() or 'irt' in c.lower()))
                    product_data['adaptive_irt'] = 'Yes' if adaptive_elem else 'Unknown'
                    
                    # Look for test type indicators
                    test_type_elem = parent.find(string=re.compile('Test Type', re.IGNORECASE)) or parent.find(class_=lambda c: c and 'test' in c.lower())
                    product_data['test_type'] = test_type_elem.text.strip() if test_type_elem else 'Unknown'
                else:
                    # If we can't find related elements, use defaults
                    product_data['remote_testing'] = 'Unknown'
                    product_data['adaptive_irt'] = 'Unknown'
                    product_data['test_type'] = 'Unknown'
                
                items.append(product_data)
        
        print(f"Extracted {len(items)} products from current page")
        
        return items
    
    def detect_last_page(self, soup, items):
        """
        Detect if this is the last page of results
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            items (list): Extracted items from the page
            
        Returns:
            bool: True if this is the last page, False otherwise
        """
        # If no items were found, likely the last page
        if not items:
            return True
            
        # Look for pagination controls and check if there's a "next" link
        pagination = soup.select_one('.pagination') or soup.find('div', class_=lambda c: c and 'pag' in c.lower())
        if pagination:
            next_link = pagination.select_one('a.next') or pagination.find('a', string=re.compile('Next', re.IGNORECASE))
            if next_link is None:
                return True
                
        # Check if we have a low number of items (less than the usual page size)
        # This is a heuristic - adjust the number if needed
        if len(items) < 5:  # Assuming normal pages have more than 5 items
            return True
            
        return False
    
    def scrape_all_catalog(self, max_pages=20):
        """
        Scrape all catalog pages with a safety limit
        
        Args:
            max_pages (int): Maximum number of pages to scrape (safety limit)
            
        Returns:
            pandas.DataFrame: DataFrame with all catalog items
        """
        all_items = []
        start = 0
        last_page = False
        page_num = 1
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        while not last_page and page_num <= max_pages:
            print(f"\n--- Scraping page {page_num} (start={start}) ---")
            
            soup = self.get_catalog_page(start=start)
            if not soup:
                print("Failed to retrieve page. Stopping.")
                break
                
            items = self.extract_catalog_items(soup)
            all_items.extend(items)
            
            # Check if this is the last page
            last_page = self.detect_last_page(soup, items)
            
            if not last_page:
                start += 10  # Move to next page (assuming 10 items per page)
                page_num += 1
                print(f"Waiting {self.delay} seconds before next request...")
                time.sleep(self.delay)  # Delay between pages
            else:
                print("Reached last page or maximum number of pages. Stopping.")
        
        # Create DataFrame from all items
        df = pd.DataFrame(all_items)
        
        # Print statistics
        print(f"\n--- Scraping Complete ---")
        print(f"Total products scraped: {len(df)}")
        print(f"Total pages scraped: {page_num}")
        
        return df
    
    def save_debug_html(self, url, filename="debug_page.html"):
        """
        Save the HTML of a page for debugging purposes
        
        Args:
            url (str): URL to fetch
            filename (str): Filename to save HTML to
        """
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Saved HTML to {filename}")
        else:
            print(f"Failed to retrieve page: {response.status_code}")

def main():
    """
    Main function to run the scraper and save results
    """
    # Create a scraper instance (with slightly longer delay between requests to be polite)
    scraper = SHLCatalogScraper(delay=3)
    
    # Run the scraper to get all catalog items
    catalog_df = scraper.scrape_all_catalog(max_pages=20)
    
    # Save to CSV
    if not catalog_df.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'output/shl_product_catalog_{timestamp}.csv'
        catalog_df.to_csv(filename, index=False)
        print(f"\nSaved {len(catalog_df)} products to {filename}")
        
        # Display the first few rowspip install -r requirements.txt
        print("\nPreview of scraped data:")
        print(catalog_df.head())
        
        # Display column stats if test_type exists
        if 'test_type' in catalog_df.columns:
            try:
                print("\nUnique test types:")
                test_types = set()
                for types in catalog_df['test_type'].dropna():
                    for t in types.split(','):
                        test_types.add(t.strip())
                print(sorted(test_types))
            except Exception as e:
                print(f"Error processing test types: {e}")
    else:
        print("No data scraped. Please check the website structure.")

# Run the script
if __name__ == "__main__":
    main()