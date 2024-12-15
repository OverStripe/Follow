import requests
from bs4 import BeautifulSoup

def get_temp_email():
    url = "https://temp-mail.org/en/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    try:
        email = soup.find("input", {"id": "mail"}).get("value")
        return email
    except AttributeError:
        return None
      
