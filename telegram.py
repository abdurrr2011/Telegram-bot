import telebot,sqlite3 ,webbrowser ,feedparser,schedule , time , threading,html,re,requests
from bs4 import BeautifulSoup
from telebot import types

# ---- Подключение к базе ----
conn = sqlite3.connect('bot_users.db', check_same_thread=False)
cursor = conn.cursor()

# ---- Создаем таблицу пользователей, если не существует ----
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT
)
''')
conn.commit()

bot = telebot.TeleBot('7491328860:AAF4A5-zLQI4IWLvPjM7eBuO9ObYH9alg_0')

ADMIN_ID = 5968583006   # твой ID


# ---------- Функция: сохранить пользователя ----------
def save_user(user):
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (user.id, user.username, user.first_name))
    conn.commit()

#Weather
def get_weather(city):
    api_key = "a3f2fb5de6e4a856cea6375190b134d2"  # өз API кілтіңді қой
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code != 200:
        return "Город не найден или ошибка API"

    data = response.json()
    city_name = data['name']
    temp = data['main']['temp']
    weather = data['weather'][0]['description']
    humidity = data['main']['humidity']
    wind = data['wind']['speed']

    return f"Погода в {city_name}:\n🌡 Температура: {temp}°C\n💧 Влажность: {humidity}%\n🌬 Ветер: {wind} м/с\n{weather.capitalize()}"



# ---------- Создаем кнопки ----------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn0=types.KeyboardButton("/weather")
    btn1 = types.KeyboardButton("/news")
    btn2 = types.KeyboardButton("/help")
    btn3 = types.KeyboardButton("/site")
    btn4 = types.KeyboardButton("Мой ID")
    btn5=types.KeyboardButton("/donate")
    markup.add(btn0,btn1, btn2)
    markup.add(btn3, btn4,btn5)
    return markup


def get_habr_news():
    # RSS-тен соңғы жаңалықты аламыз
    url = "https://habr.com/ru/rss/news/?fl=ru"
    feed = feedparser.parse(url)
    if len(feed.entries) == 0:
        return None, "Новости не найдены."

    news = feed.entries[0]
    link = news.link

    # Толық мақаланы алу
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')

    article_div = soup.find('div', class_='article-formatted-body')
    if article_div:
        full_text = article_div.get_text(separator='\n')
        full_text = html.unescape(full_text)
    else:
        full_text = html.unescape(news.summary)

    # Сурет алу (егер бар болса)
    img_tag = soup.find('img')
    image_url = img_tag['src'] if img_tag else None

    return image_url, f"{news.title}\n\n{full_text}\nСсылка: {link}"

# ---------------- /start ----------------
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user)

    # ---- КНОПКАЛАР ----
    keyboard = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🌐 Открыть сайт", url="https://google.com")
    btn2 = types.InlineKeyboardButton("ℹ️ О боте", callback_data="about_btn")

    keyboard.add(btn1)
    keyboard.add(btn2)

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Я бот, который отправляет IT-новости!\n"
        f"Команды: /help",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['donate'])
def donate(message):
    text = (
        "Спасибо за поддержку! \n\n"
        "Моя Kaspi Gold карта:\n"
        "💳 4400 4303 6091 4409\n"
        "Спасибо большое! 🙏"
    )
    bot.send_message(message.chat.id, text)


#the weather command
@bot.message_handler(commands=['weather'])
def weather(message):
    # сұраймыз қаланы
    msg = bot.send_message(message.chat.id, "Введите город для прогноза погоды:")
    bot.register_next_step_handler(msg, show_weather)

def show_weather(message):
    city = message.text
    result = get_weather(city)
    bot.send_message(message.chat.id, result)



# ---------------- /help ----------------
@bot.message_handler(commands=['help'])
def help(message):
    text = (
        "/donate — поддержать автора 💳\n"
        "/site — открыть сайт\n"
        "/about — о боте\n"
        "/news — IT новости\n"
        "/weather - Посмотреть прогноз погоды\n"
        "привет / hi — поздороваться\n"
        "id — твой ID\n"
    )

    if message.from_user.id == ADMIN_ID:
        text += "\n🔐 Админ: /admin"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())


# ---------------- /about ----------------
@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(message.chat.id, "Этот бот сделан для любителей IT!")


# ---------------- /news ----------------
@bot.message_handler(commands=['news'])
def news(message):
    image_url, text = get_habr_news()

    if image_url and image_url.startswith("http"):
        try:
            bot.send_photo(message.chat.id, photo=image_url, caption=text[:1024])
        except:
            # Егер фотосурет жіберу мүмкін болмаса, жай мәтін шығару
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, text)



# ---------------- /site ----------------
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open("https://www.youtube.com/watch?v=6rvv8bU3pKA")


# ---------------- ADMIN PANEL ----------------
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Нет доступа")

    bot.send_message(
        message.chat.id,
        "🔐 Админ панель:\n"
        "/stats — статистика\n"
        "/users — список пользователей\n"
        "/broadcast — рассылка"
    )


# ---------------- /stats ----------------
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    bot.send_message(message.chat.id, f"👥 Пользователей в базе: {count}")


# ---------------- /users ----------------
@bot.message_handler(commands=['users'])
def users(message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT user_id FROM users")
    data = cursor.fetchall()

    if not data:
        return bot.send_message(message.chat.id, "Пользователей нет.")

    text = "🧾 Список пользователей:\n" + "\n".join(str(row[0]) for row in data)
    bot.send_message(message.chat.id, text)


# ---------------- BROADCAST ----------------
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    ask = bot.send_message(message.chat.id, "Введите текст рассылки:")
    bot.register_next_step_handler(ask, send_all)


def send_all(message):
    text = message.text

    cursor.execute("SELECT user_id FROM users")
    data = cursor.fetchall()

    sent = 0
    for row in data:
        try:
            bot.send_message(row[0], text)
            sent += 1
        except:
            pass

    bot.send_message(message.chat.id, f"📨 Отправлено: {sent} пользователям")


# ---------------- ЧАТ + кнопки ----------------
@bot.message_handler()
def chat(message):
    msg = message.text.lower()

    if msg == "помощь":
        return bot.send_message(message.chat.id, "Команды: /help")

    if msg == "сайт":
        return site(message)

    if msg == "мой id":
        return bot.send_message(message.chat.id, f"ID: {message.from_user.id}")

    if msg == "привет":
        return bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!")

    if msg == "hi":
        return bot.send_message(message.chat.id, f"Hi, {message.from_user.first_name}!")

    bot.send_message(message.chat.id, "Не понял 🙃. Напиши /help")


def auto_news():
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    image_url, text = get_habr_news()

    for row in users:
        try:
            if image_url:
                bot.send_photo(row[0], photo=image_url, caption=text)
            else:
                bot.send_message(row[0], text)
        except:
            pass

def scheduler():
    schedule.every(1).hours.do(auto_news)
    while True:
        schedule.run_pending()
        time.sleep(1)

t = threading.Thread(target=scheduler)
t.start()




bot.polling(non_stop=True)