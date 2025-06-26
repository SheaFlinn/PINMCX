import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import PyPDF2
import re
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)

class CouncilAgendaScraper:
    def __init__(self):
        self.base_url = "https://www.memphistn.gov/"
        self.agenda_url = "https://www.memphistn.gov/government/city-council/agendas"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.draft_contracts = []
        
    def get_agenda_page(self):
        """Fetch the council agenda page"""
        headers = {'User-Agent': self.user_agent}
        try:
            response = requests.get(self.agenda_url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching agenda page: {str(e)}")
            raise

    def extract_pdf_links(self, html):
        """Extract links to agenda PDFs from the page"""
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []
        
        # Look for agenda links (this may need to be adjusted based on the actual page structure)
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf') and 'agenda' in href.lower():
                full_url = urljoin(self.base_url, href)
                pdf_links.append(full_url)
        
        return pdf_links

    def parse_pdf(self, pdf_url):
        """Download and parse a PDF agenda for contract-worthy items"""
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Save the PDF temporarily
            with open('temp_agenda.pdf', 'wb') as f:
                f.write(response.content)
            
            # Parse the PDF
            with open('temp_agenda.pdf', 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            # Clean up
            os.remove('temp_agenda.pdf')
            
            return text
        except Exception as e:
            logging.error(f"Error parsing PDF from {pdf_url}: {str(e)}")
            return ""

    def extract_contract_items(self, text, agenda_date):
        """Extract contract-worthy items from agenda text"""
        # Define patterns for contract-worthy items
        patterns = {
            'ordinance': r'Ordinance\s+\d+',
            'resolution': r'Resolution\s+\d+',
            'zoning': r'Zoning\s+\d+',
            'vote': r'Vote\s+\d+',
            'approval': r'Approval\s+\d+'
        }
        
        contracts = []
        
        # Search for patterns
        for item_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                # Get the surrounding context
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Generate a suggested contract phrasing
                suggested_phrase = self.generate_contract_phrase(context, item_type)
                
                if suggested_phrase:
                    contracts.append({
                        'title': f"Council {item_type.title()} {match.group(0)}",
                        'description': context,
                        'agenda_date': agenda_date.strftime('%Y-%m-%d'),
                        'source_url': pdf_url,
                        'suggested_contract': suggested_phrase,
                        'item_type': item_type,
                        'scraped_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    })
        
        return contracts

    def generate_contract_phrase(self, context, item_type):
        """Generate a suggested contract phrase from agenda context"""
        # Basic template for contract phrases
        templates = {
            'ordinance': "Will the Memphis City Council pass Ordinance {}?",
            'resolution': "Will the Memphis City Council approve Resolution {}?",
            'zoning': "Will the Memphis City Council approve Zoning {}?",
            'vote': "Will the Memphis City Council vote in favor of {}?",
            'approval': "Will the Memphis City Council approve {}?"
        }
        
        # Extract the item number
        item_number = re.search(r'\d+', context)
        if not item_number:
            return None
            
        # Format the template
        return templates[item_type].format(item_number.group(0))

    def save_drafts(self):
        """Save extracted contracts to JSON file"""
        try:
            os.makedirs('drafts', exist_ok=True)
            with open('drafts/council_agenda_drafts.json', 'w', encoding='utf-8') as f:
                json.dump(self.draft_contracts, f, indent=4)
            
            logging.info(f"Saved {len(self.draft_contracts)} draft contracts to drafts/council_agenda_drafts.json")
            
        except Exception as e:
            logging.error(f"Error saving draft contracts: {str(e)}")
            raise

    def run(self):
        """Run the complete scraping process"""
        try:
            # Get agenda page
            html = self.get_agenda_page()
            
            # Extract PDF links
            pdf_links = self.extract_pdf_links(html)
            logging.info(f"Found {len(pdf_links)} agenda PDFs")
            
            # Process each PDF
            for pdf_url in pdf_links:
                logging.info(f"Processing PDF: {pdf_url}")
                
                # Parse PDF
                text = self.parse_pdf(pdf_url)
                
                # Extract date from URL or filename
                agenda_date = datetime.now()  # Default to current date
                filename = pdf_url.split('/')[-1]
                date_match = re.search(r'\d{8}', filename)
                if date_match:
                    try:
                        agenda_date = datetime.strptime(date_match.group(0), '%Y%m%d')
                    except ValueError:
                        pass
                
                # Extract contract items
                contracts = self.extract_contract_items(text, agenda_date)
                self.draft_contracts.extend(contracts)
            
            # Save results
            self.save_drafts()
            
        except Exception as e:
            logging.error(f"Error in main process: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = CouncilAgendaScraper()
    scraper.run()
