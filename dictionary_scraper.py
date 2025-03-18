import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DictionaryScraper:
    def __init__(self):
        self.base_url = "https://dictionary.cambridge.org/dictionary/english/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.crawled_words = set()
        self.vocabulary_limit = int(os.getenv('VOCABULARY_LIMIT', 50))
        self.sleep_time = float(os.getenv('REQUEST_SLEEP_TIME', 1))

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

    def crawl_dictionary(self, start_word):
        all_word_data = []
        words_to_crawl = [start_word]
        
        while words_to_crawl and len(self.crawled_words) < self.vocabulary_limit:
            current_word = words_to_crawl.pop(0)
            
            if current_word in self.crawled_words:
                continue
                
            print(f"Crawling word: {current_word}")
            word_data = self.extract_word_info(current_word)
            
            if word_data:
                all_word_data.append(word_data)
                self.crawled_words.add(current_word)
                
                try:
                    response = requests.get(f"{self.base_url}{current_word}", headers=self.headers)
                    soup = BeautifulSoup(response.text, 'lxml')
                    related_words = self.extract_related_words(soup)
                    words_to_crawl.extend([w for w in related_words if w not in self.crawled_words])
                    
                except requests.RequestException as e:
                    print(f"Error fetching related words for '{current_word}': {str(e)}")
                
            time.sleep(self.sleep_time)
            
        return all_word_data

def main():
    scraper = DictionaryScraper()
    word = "thesaurus"  # Example word
    word_data = scraper.extract_word_info(word)
    scraper.save_to_json(word_data, f"{word}_data.json")

if __name__ == "__main__":
    main() 