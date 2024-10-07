import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.model_selection import train_test_split

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class SECEdgarScraper:
    def __init__(self, output_dir='finance_data'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.stop_words = set(stopwords.words('english'))

    def download_filing(self, url, save_path):
        response = requests.get(url)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

    def extract_relevant_sections(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract Management's Discussion and Analysis
        mda = soup.find('a', {'name': re.compile('mda', re.I)})
        mda_text = ""
        if mda:
            mda_section = mda.find_next('div', {'class': 'section'})
            if mda_section:
                mda_text = mda_section.get_text()

        # Extract Risk Factors
        risk = soup.find('a', {'name': re.compile('risk', re.I)})
        risk_text = ""
        if risk:
            risk_section = risk.find_next('div', {'class': 'section'})
            if risk_section:
                risk_text = risk_section.get_text()

        return mda_text + "\n\n" + risk_text

    def clean_text(self, text):
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.stop_words]
        return ' '.join(tokens)

    def process_filings(self, urls):
        data = []
        for url in tqdm(urls, desc="Processing filings"):
            file_name = url.split('/')[-1]
            save_path = os.path.join(self.output_dir, file_name)
            
            try:
                self.download_filing(url, save_path)
                extracted_text = self.extract_relevant_sections(save_path)
                cleaned_text = self.clean_text(extracted_text)
                
                if len(cleaned_text.split()) > 100:  # Only keep substantive texts
                    data.append(cleaned_text)
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
            
            # Remove the downloaded file to save space
            os.remove(save_path)
        
        return data

    def prepare_dataset(self, data, train_size=0.8, val_size=0.1, test_size=0.1):
        df = pd.DataFrame(data, columns=['text'])
        
        # Split the data
        train_val, test = train_test_split(df, test_size=test_size, random_state=42)
        train, val = train_test_split(train_val, test_size=val_size/(train_size+val_size), random_state=42)
        
        # Save the datasets
        train.to_csv(os.path.join(self.output_dir, 'train.csv'), index=False)
        val.to_csv(os.path.join(self.output_dir, 'val.csv'), index=False)
        test.to_csv(os.path.join(self.output_dir, 'test.csv'), index=False)
        
        print(f"Train set size: {len(train)}")
        print(f"Validation set size: {len(val)}")
        print(f"Test set size: {len(test)}")

def main():
    # List of SEC EDGAR filing URLs (you would need to compile this list)
    urls = [
        "https://www.sec.gov/Archives/edgar/data/example1.htm",
        "https://www.sec.gov/Archives/edgar/data/example2.htm",
        # Add more URLs here
    ]

    scraper = SECEdgarScraper()
    data = scraper.process_filings(urls)
    scraper.prepare_dataset(data)

if __name__ == "__main__":
    main()