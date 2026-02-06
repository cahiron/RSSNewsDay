from bs4 import BeautifulSoup
from telebot import types
from time import gmtime
from urllib.parse import urlparse, urlunparse # Para normalização de URLs
import feedparser
import os
import re
import telebot
import telegraph
import time
import random
import requests
import sqlite3
import xml.etree.ElementTree as ET  # Adicionado para validação XML

def create_table_if_not_exists():
    conn = sqlite3.connect('rss2telegram.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        link TEXT PRIMARY KEY
    )
    ''')
    conn.commit()
    conn.close()

create_table_if_not_exists() # Garantir que tabela exista com link único

def normalize_url(url):
    parts = urlparse(url)
    clean_query = '&'.join([q for q in parts.query.split('&') if not q.startswith('utm_') and q != ''])
    return urlunparse(parts._replace(query=clean_query))

def get_variable(variable):
    if not os.environ.get(f'{variable}'):
        var_file = open(f'{variable}.txt', 'r')
        return var_file.read()
    return os.environ.get(f'{variable}')

URL = get_variable('URL')
DESTINATION = get_variable('DESTINATION')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
EMOJIS = os.environ.get('EMOJIS', '🗞,📰,🗒,🗓,📋,🔗,📝,🗃')
PARAMETERS = os.environ.get('PARAMETERS', False)
HIDE_BUTTON = os.environ.get('HIDE_BUTTON', False)
DRYRUN = os.environ.get('DRYRUN')
TOPIC = os.environ.get('TOPIC', False)
TELEGRAPH_TOKEN = os.environ.get('TELEGRAPH_TOKEN', False)

bot = telebot.TeleBot(BOT_TOKEN)

def add_to_history(link):
    conn = sqlite3.connect('rss2telegram.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO history (link) VALUES (?)', (link,))
    conn.commit()
    conn.close()

def check_history(link):
    conn = sqlite3.connect('rss2telegram.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM history WHERE link = ?', (link,))
    data = cursor.fetchone()
    conn.close()
    return data

def firewall(text):
    try:
        rules = open(f'RULES.txt', 'r')
    except FileNotFoundError:
        return True
    result = None
    for rule in rules.readlines():
        opt, arg = rule.split(':')
        arg = arg.strip()
        if arg == 'ALL' and opt == 'DROP':
            result = False
        elif arg == 'ALL' and opt == 'ACCEPT':
            result = True
        elif arg.lower() in text.lower() and opt == 'DROP':
            result = False
        elif arg.lower() in text.lower() and opt == 'ACCEPT':
            result = True
    return result

def create_telegraph_post(topic):
    telegraph_auth = telegraph.Telegraph(
        access_token=f'{get_variable("TELEGRAPH_TOKEN")}'
    )
    response = telegraph_auth.create_page(
        f'{topic["title"]}',
        html_content=(
            f'{topic["summary"]}'
            + f'Ver original ({topic["site_name"]})'
        ),
        author_name=f'{topic["site_name"]}'
    )
    return response["url"]

# ===========================
# NOVO: Função para envio seguro com tratamento de rate limit do Telegram
# ===========================
def send_message(topic, button):
    if DRYRUN == 'failure':
        return
    MESSAGE_TEMPLATE = os.environ.get(f'MESSAGE_TEMPLATE', False)
    if MESSAGE_TEMPLATE:
        MESSAGE_TEMPLATE = set_text_vars(MESSAGE_TEMPLATE, topic)
    else:
        MESSAGE_TEMPLATE = f'{topic["title"]}'
    if TELEGRAPH_TOKEN:
        iv_link = create_telegraph_post(topic)
        MESSAGE_TEMPLATE = f'{MESSAGE_TEMPLATE}'
    if not firewall(str(topic)):
        print(f'xxx {topic["title"]}')
        return
    btn_link = button
    if button:
        btn_link = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(f'{button}', url=topic['link'])
        btn_link.row(btn)

    # --- INÍCIO DA MUDANÇA: tratamento de erro 429 (rate limit) ---
    def try_send(dest, send_func, *args, **kwargs):
        import re
        while True:
            try:
                send_func(*args, **kwargs)
                break
            except telebot.apihelper.ApiTelegramException as e:
                if "Too Many Requests" in str(e):
                    match = re.search(r'retry after (\\d+)', str(e))
                    if match:
                        wait_time = int(match.group(1))
                        print(f"Aguardando {wait_time} segundos devido ao limite do Telegram...")
                        time.sleep(wait_time)
                    else:
                        print("Erro de limite do Telegram, aguardando 10 segundos.")
                        time.sleep(10)
                else:
                    print(f"Erro ao enviar mensagem: {e}")
                    break
    # --- FIM DA MUDANÇA ---

    if HIDE_BUTTON or TELEGRAPH_TOKEN:
        for dest in DESTINATION.split(','):
            try_send(dest, bot.send_message, dest, MESSAGE_TEMPLATE, parse_mode='HTML', reply_to_message_id=TOPIC)
            time.sleep(1.2)  # NOVO: Delay para evitar atingir o limite
    else:
        if topic['photo'] and not TELEGRAPH_TOKEN:
            response = requests.get(topic['photo'], headers = {'User-agent': 'Mozilla/5.1'})
            open('img', 'wb').write(response.content)
            for dest in DESTINATION.split(','):
                photo = open('img', 'rb')
                try:
                    try_send(dest, bot.send_photo, dest, photo, caption=MESSAGE_TEMPLATE, parse_mode='HTML', reply_markup=btn_link, reply_to_message_id=TOPIC)
                except telebot.apihelper.ApiTelegramException:
                    topic['photo'] = False
                    send_message(topic, button)
                time.sleep(1.2)  # NOVO: Delay para evitar atingir o limite
        else:
            for dest in DESTINATION.split(','):
                try_send(dest, bot.send_message, dest, MESSAGE_TEMPLATE, parse_mode='HTML', reply_markup=btn_link, disable_web_page_preview=True, reply_to_message_id=TOPIC)
                time.sleep(1.2)  # NOVO: Delay para evitar atingir o limite
    print(f'... {topic["title"]}')

# ===========================
# FIM das mudanças de tratamento de rate limit
# ===========================

# Função para obter imagem do link
# Adicionado tratamento genérico de exceção para evitar travamentos
def get_img(url):
    try:
        response = requests.get(url, headers = {'User-agent': 'Mozilla/5.1'}, timeout=3)
        html = BeautifulSoup(response.content, 'html.parser')
        photo = html.find('meta', {'property': 'og:image'})['content']
    except TypeError:
        photo = False
    except requests.exceptions.ReadTimeout:
        photo = False
    except requests.exceptions.TooManyRedirects:
        photo = False
    except Exception:
        photo = False  # NOVO: captura outros erros
    return photo

def define_link(link, PARAMETERS):
    if PARAMETERS:
        if '?' in link:
            return f'{link}&amp;{PARAMETERS}'
        return f'{link}?{PARAMETERS}'
    return f'{link}'

def set_text_vars(text, topic):
    cases = {
        'SITE_NAME': topic['site_name'],
        'TITLE': topic['title'],
        'SUMMARY': re.sub('&lt;[^&lt;]+?&gt;', '', topic['summary']),
        'LINK': define_link(topic['link'], PARAMETERS),
        'EMOJI': random.choice(EMOJIS.split(","))
    }
    for word in re.split('{|}', text):
        try:
            text = text.replace(word, cases.get(word))
        except TypeError:
            continue
    return text.replace('\\n', '\n').replace('{', '').replace('}', '')

# ===========================
# NOVO: Função para validar se o feed é XML válido antes de processar
# ===========================
def is_valid_rss(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f'ERRO HTTP {resp.status_code}: {url}')
            return False
        if 'xml' not in resp.headers.get('Content-Type', ''):
            print(f'ERRO: {url} não retorna XML.')
            return False
        ET.fromstring(resp.content)
        return True
    except Exception as e:
        print(f'ERRO ao validar XML de {url}: {e}')
        return False

# ===========================
# NOVO: Função para parse seguro do feed
# ===========================
def safe_parse_feed(url):
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"ERRO: {url} não parece um feed RSS válido. Detalhe: {feed.bozo_exception}")
            return None
        return feed
    except Exception as e:
        print(f"ERRO ao processar {url}: {e}")
        return None

def check_topics(url):
    now = gmtime()
    # NOVO: validação prévia antes de tentar parsear
    if not is_valid_rss(url):
        print(f'ERRO: {url} não parece um feed RSS válido.')
        return
    feed = safe_parse_feed(url)
    if feed is None or 'feed' not in feed or 'title' not in feed['feed']:
        print(f'\nERRO: {url} não parece um feed RSS válido.')
        return
    source = feed['feed']['title']
    print(f'\nChecando {source}:{url}')
    for tpc in reversed(feed['items'][:10]):
        link = normalize_url(tpc.links[0].href)  # normaliza o link
        if check_history(link):
            continue
        add_to_history(link)
    # restante do código usando 'link' no lugar de tpc.links[0].href
    topic = {
        topic['site_name'] = feed['feed']['title']
        topic['title'] = tpc.title.strip()
        topic['summary'] = tpc.summary
        topic['link'] = link
        topic['photo'] = get_img(link)
    }
    
    BUTTON_TEXT = os.environ.get('BUTTON_TEXT', False)
    if BUTTON_TEXT:
        BUTTON_TEXT = set_text_vars(BUTTON_TEXT, topic)
    try:
        send_message(topic, BUTTON_TEXT)
    except telebot.apihelper.ApiTelegramException as e:
        print(e)
        pass

if __name__ == "__main__":
    for url in URL.split():
        check_topics(url)

