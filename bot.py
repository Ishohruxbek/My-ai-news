import os
import time
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY не найден. Добавьте его в секреты GitHub.")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}, timeout=15)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'photo': photo_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=15)
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")

def ask_ai(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    for attempt in range(2):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "Ошибка: Неверный API-ключ Groq. Проверьте секрет GROQ_API_KEY."
            if e.response.status_code == 404:
                return "Ошибка: Модель не найдена. Проверьте название модели."
            time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return "Не удалось получить ответ от ИИ после нескольких попыток."

def get_github_trends():
    try:
        url = "https://github.com/trending?since=daily"
        soup = BeautifulSoup(requests.get(url, timeout=20).text, 'html.parser')
        articles = soup.find_all('article', class_='Box-row')[:3]
        result = []
        for article in articles:
            repo_name = article.find('h2').find('a').text.strip().replace('\n', '').replace(' ', '')
            desc_tag = article.find('p', class_='col-9')
            description = desc_tag.text.strip() if desc_tag else "Без описания"
            prompt = f"Объясни этот проект на GitHub максимально просто для новичка. Название: {repo_name}. Описание: {description}. Напиши 1 предложение что это, и 1 предложение зачем нужно. Пиши на русском."
            ai_text = ask_ai(prompt)
            result.append(f"🐙 **{repo_name}**\n💡 {ai_text}\n🔗 https://github.com/{repo_name}")
        return "\n\n".join(result)
    except Exception as e:
        return f"Ошибка GitHub: {e}"

def get_space_news():
    for attempt in range(2):
        try:
            response = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('media_type') == 'image':
                prompt = f"Переведи на русский и объясни максимально просто: {data.get('explanation', '')}"
                ai_text = ask_ai(prompt)
                send_photo(data['url'], f"🚀 **{data.get('title', 'Космос')}**\n\n{ai_text}")
            else:
                video_url = data.get('url') or "Ссылка скрыта"
                send_message(f"Сегодня NASA выложило видео (не фото):\n{video_url}")
            return
        except requests.exceptions.ReadTimeout:
            if attempt == 0:
                time.sleep(5)
                continue
            send_message("Ошибка: Сервер NASA не отвечает. Попробуйте позже.")
        except Exception as e:
            send_message(f"Ошибка NASA: {e}")
            return

if __name__ == "__main__":
    github_text = get_github_trends()
    if github_text: send_message(github_text)
    get_space_news()
