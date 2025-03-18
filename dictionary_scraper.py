import requests
from bs4 import BeautifulSoup
import json
import re

class DictionaryScraper:
    def __init__(self):
        self.base_url = "https://dictionary.cambridge.org/dictionary/english/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def clean_text(self, text):
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def extract_pronunciation(self, entry):
        pronunciations = {'uk': '', 'us': ''}
        
        uk_pron = entry.find('span', {'class': 'uk dpron-i'})
        us_pron = entry.find('span', {'class': 'us dpron-i'})
        
        if uk_pron:
            ipa = uk_pron.find('span', {'class': 'ipa'})
            if ipa:
                pronunciations['uk'] = self.clean_text(ipa.text)
                
        if us_pron:
            ipa = us_pron.find('span', {'class': 'ipa'})
            if ipa:
                pronunciations['us'] = self.clean_text(ipa.text)
                
        return pronunciations

    def extract_word_info(self, word):
        try:
            url = f"{self.base_url}{word}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            word_data = {
                'word': word,
                'entries': []
            }
            
            entries = soup.find_all('div', {'class': 'pr entry-body__el'})
            
            for entry in entries:
                entry_data = {}
                
                header = entry.find('span', {'class': 'hw dhw'})
                if header:
                    entry_data['word'] = self.clean_text(header.text)
                
                pos = entry.find('span', {'class': 'pos dpos'})
                if pos:
                    entry_data['part_of_speech'] = self.clean_text(pos.text)
                
                pronunciations = self.extract_pronunciation(entry)
                entry_data['pronunciation'] = pronunciations
                
                definitions = []
                for def_block in entry.find_all('div', {'class': 'def ddef_d db'}):
                    definitions.append(self.clean_text(def_block.text))
                entry_data['definitions'] = definitions
                
                examples = []
                for example in entry.find_all('div', {'class': 'examp dexamp'}):
                    examples.append(self.clean_text(example.text))
                entry_data['examples'] = examples
                
                word_data['entries'].append(entry_data)
            
            return word_data
            
        except requests.RequestException as e:
            print(f"Error fetching data for word '{word}': {str(e)}")
            return None

    def save_to_json(self, word_data, filename):
        if word_data:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(word_data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        else:
            print("No data to save")

def main():
    scraper = DictionaryScraper()
    word = "thesaurus"  # Example word
    word_data = scraper.extract_word_info(word)
    scraper.save_to_json(word_data, f"{word}_data.json")

if __name__ == "__main__":
    main() 