import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
CHAT_ID = os.environ.get('CHAT_ID')

# Увеличили таймаут до 60 секунд, чтобы сервер успел ответить
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'timeout': 60})

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}, timeout=15)
    except Exception:
        pass

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'photo': photo_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=15)
    except Exception:
        pass

def ask_ai(prompt):
    # Используем стабильную модель 2.0
    for attempt in range(2):
        try:
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            return response.text
        except Exception as e:
            time.sleep(3)
    return "Не удалось получить ответ от ИИ (сервер перегружен)."

def get_github_trends():
    try:
        url = "https://github.com/trending?since=daily"
        soup = BeautifulSoup(requests.get(url, timeout=15).text, 'html.parser')
        articles = soup.find_all('article', class_='Box-row')[:3]
        result = []
        for article in articles:
            repo_name = article.find('h2').find('a').text.strip().replace('\n', '').replace(' ', '')
            desc_tag = article.find('p', class_='col-9')
            description = desc_tag.text.strip() if desc_tag else "Без описания"
            prompt = f"Объясни просто для новичка: {repo_name}. {description}. 1 предложение что это, 1 зачем нужно."
            
            ai_text = ask_ai(prompt)
            result.append(f"🐙 **{repo_name}**\n💡 {ai_text}\n🔗 https://github.com/{repo_name}")
        return "\n\n".join(result)
    except Exception as e:
        return f"Ошибка GitHub: {e}"

def get_space_news():
    try:
        data = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=15).json()
        if data.get('media_type') == 'image':
            prompt = f"Переведи и объясни просто на русском: {data.get('explanation', '')}"
            ai_text = ask_ai(prompt)
            send_photo(data['url'], f"🚀 **{data.get('title', 'Космос')}**\n\n{ai_text}")
        else:
            video_url = data.get('url') or "Ссылка скрыта"
            send_message(f"Сегодня NASA выложило видео (не фото):\n{video_url}")
    except Exception as e:
        send_message(f"Ошибка NASA: {e}")

if __name__ == "__main__":
    github_text = get_github_trends()
    if github_text: send_message(github_text)
    get_space_news()
