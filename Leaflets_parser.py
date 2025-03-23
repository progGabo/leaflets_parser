import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

class LeafletsParser:
    BASE_URL = "https://www.prospektmaschine.de/"

    def __init__(self):
        self.session = requests.Session()

    def fetch_page(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return response.text
    
    def run(self):
        shops = self.get_shops()
        all_leaflets = []
        
        for shop_name, shop_url in shops.items():
            print(f"Fetching leaflets for {shop_name}...")
            html = self.fetch_page(self.BASE_URL + shop_url)
            leaflets = self.parse(html, shop_name)
            all_leaflets.extend(leaflets)
        
        self.save_to_json(all_leaflets)
        print(f"Successfully saved {len(all_leaflets)} leaflets to JSON file.")

    def get_shops(self):
        html = self.fetch_page(self.BASE_URL + "hypermarkte/")
        soup = BeautifulSoup(html, 'html.parser')
        shop_links = soup.select("#left-category-shops a")
        shops = {link.text.strip(): link.get("href") for link in shop_links if link.get("href")}
        return shops

    def parse(self, html, shop_name):
        soup = BeautifulSoup(html, 'html.parser')
        leaflets = []

        brochures = soup.find_all(class_="brochure-thumb")
        for item in brochures:
            try:
                if item.select(".grid-item-old") != []:
                    continue

                title = item.select_one(".grid-item-content strong").text.strip()
                img_tag = item.find("img")
                thumbnail = img_tag.get("src") or img_tag.get("data-src")
                
                date_text = item.select_one(".hidden-sm").text.strip()
                date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})", date_text)

                if date_match:
                    valid_from, valid_to = date_match.groups()
                else:
                    date_match = re.search(r".*?(\d{2}\.\d{2}\.\d{4})", date_text)
                    valid_from, valid_to = "", date_match.group(1) if date_match else ("", "")

                valid_to = datetime.strptime(valid_to, '%d.%m.%Y').strftime('%Y-%m-%d')

                if valid_from != '':
                    valid_from = datetime.strptime(valid_from, '%d.%m.%Y').strftime('%Y-%m-%d')

                parsed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                leaflets.append({
                    "title": title,
                    "thumbnail": thumbnail,
                    "shop_name": shop_name,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "parsed_time": parsed_time
                })
            except Exception as e:
                print(f"Error parsing item: {e}")
        
        return leaflets
    
    def save_to_json(self, data, filename="leaflets.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    

if __name__ == "__main__":
    parser = LeafletsParser()
    parser.run()