import json
import cloudscraper
import concurrent.futures
import requests
from copy import deepcopy
from re import match as rematch, sub as resub, compile as recompile
from asyncio import sleep as asleep
from time import sleep
from urllib.parse import unquote, quote
from requests import get as rget, post as rpost
from bs4 import BeautifulSoup, NavigableString, Tag
from base64 import b64decode, b64encode

from telegram import Message
from telegram.ext import CommandHandler, Updater
from telegram.ext.filters import Filters
from bot import LOGGER, config_dict, OWNER_ID
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.ext_utils.bot_utils import is_paid, is_sudo, get_readable_file_size
from bot.helper.mirror_utils.download_utils.direct_link_generator import rock, try2link, ez4, ouo

# Define regex patterns
DDL_REGEX = recompile(r"DDL\(([^),]+), ([^),]+), ([^),]+), ([^),]+)\)")
POST_ID_REGEX = recompile(r'"postId":"(\d+)"')

# Initialize global variables
next_page = False
next_page_token = ""
post_id = ""
data_dict = {}
main_dict = {}

def scrapper(update, context):
    user_id = update.message.from_user.id
    if config_dict['PAID_SERVICE'] and user_id != OWNER_ID and not is_sudo(user_id) and not is_paid(user_id):
        sendMessage(f"Buy Paid Service to Use this Scrape Feature.", context.bot, update.message)
        return

    message: Message = update.effective_message
    link = extract_link_from_message(message)
    if not link:
        send_help_message(context.bot, update.message)
        return

    if not is_valid_link(link):
        sendMessage('Not a Valid Link.', context.bot, update.message)
        return

    if "sharespark" in link:
        scrape_sharespark(link, context, update)
    elif "teluguflix" in link:
        scrape_teluguflix(link, context, update)
    elif "cinevood" in link:
        scrape_cinevood(link, context, update)
    elif "atishmkv" in link:
        scrape_atishmkv(link, context, update)
    elif "taemovies" in link:
        scrape_taemovies(link, context, update)
    elif "toonworld4all" in link:
        scrape_toonworld4all(link, context, update)
    elif "skymovieshd" in link:
        scrape_skymovieshd(link, context, update)
    elif "animekaizoku" in link:
        scrape_animekaizoku(link, context, update)
    elif "animeremux" in link:
        scrape_animeremux(link, context, update)
    elif rematch(r'https?://.+\/\d+\:\/', link):
        scrape_index(link, context, update, message.text.split('\n'))
    else:
        scrape_generic(link, context, update)

def extract_link_from_message(message):
    if message.reply_to_message:
        return message.reply_to_message.text
    else:
        parts = message.text.split('\n')
        return parts[0].split(' ', 1)[1] if len(parts) > 1 else None

def send_help_message(bot, message):
    help_msg = "<b>Send link after command:</b>\n"
    help_msg += f"<code>/{BotCommands.ScrapeCommand[0]} {{link}}</code>\n"
    help_msg += "<b>By Replying to Message (Including Link):</b>\n"
    help_msg += f"<code>/{BotCommands.ScrapeCommand[0]} {{message}}</code>"
    sendMessage(help_msg, bot, message)

def is_valid_link(link):
    return rematch(r"^(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", link) is not None

def scrape_sharespark(link, context, update):
    gd_txt = ""
    res = rget("?action=printpage;".join(link.split('?')))
    soup = BeautifulSoup(res.text, 'html.parser')
    for br in soup.findAll('br'):
        next_s = br.nextSibling
        if not (next_s and isinstance(next_s, NavigableString)):
            continue
        next2_s = next_s.nextSibling
        if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
            if str(next_s).strip():
                List = next_s.split()
                if rematch(r'^(480p|720p|1080p)(.+)? Links:\Z', next_s):
                    gd_txt += f'<b>{next_s.replace("Links:", "GDToT Links :")}</b>\n\n'
                for s in List:
                    ns = resub(r'\(|\)', '', s)
                    if rematch(r'https?://.+\.gdtot\.\S+', ns):
                        r = rget(ns)
                        soup = BeautifulSoup(r.content, "html.parser")
                        title = soup.select('meta[property^="og:description"]')
                        gd_txt += f"<code>{(title[0]['content']).replace('Download ', '')}</code>\n{ns}\n\n"
                    elif rematch(r'https?://pastetot\.\S+', ns):
                        nxt = resub(r'\(|\)|(https?://pastetot\.\S+)', '', next_s)
                        gd_txt += f"\n<code>{nxt}</code>\n{ns}\n"
        if len(gd_txt) > 4000:
            sendMessage(gd_txt, context.bot, update.message)
            gd_txt = ""
    if gd_txt:
        sendMessage(gd_txt, context.bot, update.message)

def scrape_teluguflix(link, context, update):
    sent = sendMessage('Running Scrape ...', context.bot, update.message)
    gd_txt = ""
    r = rget(link)
    soup = BeautifulSoup(r.text, "html.parser")
    links = soup.select('a[href*="gdtot"]')
    gd_txt = f"Total Links Found : {len(links)}\n\n"
    editMessage(gd_txt, sent)
    for no, link in enumerate(links, start=1):
        gdlk = link['href']
        t = rget(gdlk)
        soupt = BeautifulSoup(t.text, "html.parser")
        title = soupt.select('meta[property^="og:description"]')
        gd_txt += f"{no}. <code>{(title[0]['content']).replace('Download ', '')}</code>\n{gdlk}\n\n"
        editMessage(gd_txt, sent)
        sleep(1.5)
        if len(gd_txt) > 4000:
            sent = sendMessage("<i>Running More Scrape ...</i>", context.bot, update.message)
            gd_txt = ""
    if gd_txt:
        sendMessage(gd_txt, context.bot, update.message)

def scrape_cinevood(link, context, update):
    prsd = ""
    links = []
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    x = soup.select('a[href^="https://filepress"]')
    for a in x:
        links.append(a['href'])
    for o in links:
        res = rget(o)
        soup = BeautifulSoup(res.content, "html.parser")
        title = soup.title
        prsd += f'{title}\n{o}\n\n'
        if len(prsd) > 4000:
            sendMessage(prsd, context.bot, update.message)
            prsd = ""
    if prsd:
        sendMessage(prsd, context.bot, update.message)

def scrape_atishmkv(link, context, update):
    prsd = ""
    links = []
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    x = soup.select('a[href^="https://gdflix"]')
    for a in x:
        links.append(a['href'])
    for o in links:
        prsd += o + '\n\n'
        if len(prsd) > 4000:
            sendMessage(prsd, context.bot, update.message)
            prsd = ""
    if prsd:
        sendMessage(prsd, context.bot, update.message)

def scrape_taemovies(link, context, update):
    sent = sendMessage('Running Scrape ...', context.bot, update.message)
    gd_txt, no = "", 0
    r = rget(link)
    soup = BeautifulSoup(r.text, "html.parser")
    links = soup.select('a[href*="shortingly"]')
    gd_txt = f"Total Links Found : {len(links)}\n\n"
    editMessage(gd_txt, sent)
    for no, link in enumerate(links, start=1):
        gdlk = link['href']
        title = link.find_parent('div').find_previous_sibling('div').text
        gd_txt += f"{no}. <code>{title.strip()}</code>\n{gdlk}\n\n"
        editMessage(gd_txt, sent)
        sleep(1.5)
        if len(gd_txt) > 4000:
            sent = sendMessage("<i>Running More Scrape ...</i>", context.bot, update.message)
            gd_txt = ""
    if gd_txt:
        sendMessage(gd_txt, context.bot, update.message)

def scrape_toonworld4all(link, context, update):
    prsd = ""
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    x = soup.select('a[href*="shortingly"]')
    for a in x:
        prsd += a['href'] + '\n\n'
        if len(prsd) > 4000:
            sendMessage(prsd, context.bot, update.message)
            prsd = ""
    if prsd:
        sendMessage(prsd, context.bot, update.message)

def scrape_skymovieshd(link, context, update):
    prsd = ""
    links = []
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    x = soup.select('a[href*="shortingly"]')
    for a in x:
        links.append(a['href'])
    for o in links:
        prsd += o + '\n\n'
        if len(prsd) > 4000:
            sendMessage(prsd, context.bot, update.message)
            prsd = ""
    if prsd:
        sendMessage(prsd, context.bot, update.message)

def scrape_animekaizoku(link, context, update):
    data_dict.clear()
    main_dict.clear()
    next_page = False
    next_page_token = ""
    post_id = ""
    final_link = ""
    gd_txt = ""
    sent = sendMessage('Running Scrape ...', context.bot, update.message)
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    load_more_btn = soup.select('button.load-more-posts')
    post_id = POST_ID_REGEX.findall(str(load_more_btn))[0]
    for looper in range(15):
        loop_result = looper(link, looper)
        if not loop_result:
            break
    for k, v in data_dict.items():
        if v not in main_dict.keys():
            main_dict[v] = k
    for k, v in main_dict.items():
        final_link += f"<b>{v}</b>\n{k}\n\n"
        if len(final_link) > 4000:
            sendMessage(final_link, context.bot, update.message)
            final_link = ""
    if final_link:
        sendMessage(final_link, context.bot, update.message)

def looper(link, looper):
    next_page = True
    while next_page:
        gd_dict = {}
        post_id, page, gd_txt, url = "", "", "", ""
        res = rpost(f"https://animekaizoku.com/wp-admin/admin-ajax.php", data={"action": "load_more", "page": next_page_token, "post_id": post_id, "nonce": "dcd3b7f1e1"})
        data = res.json()
        if data.get("data"):
            soup = BeautifulSoup(data['data'], 'html.parser')
            for lnk in soup.select('a[href*="https://www.gd"]'):
                link = lnk['href']
                if resub(r'\(|\)', '', link) in gd_dict:
                    continue
                gd_dict[link] = ""
            next_page_token = data['nextPage']
            next_page = data['hasNextPage']
        else:
            next_page = False
    data_dict.update(gd_dict)
    return gd_dict

def scrape_animeremux(link, context, update):
    final_link = ""
    res = rget(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    for a in soup.findAll('a', href=True):
        url = a['href']
        if "https://gdflix" in url:
            final_link += f"<code>{url}</code>\n\n"
    if final_link:
        sendMessage(final_link, context.bot, update.message)

def scrape_index(link, context, update, message_text_lines):
    user, password = None, None
    if len(message_text_lines) > 1:
        user_pass = message_text_lines[1].split(" ")
        if len(user_pass) == 2:
            user, password = user_pass[0], user_pass[1]
    gd_txt = ""
    sent = sendMessage('Running Scrape ...', context.bot, update.message)
    gd_txt = indexScrape(link, user, password)
    if len(gd_txt) > 4000:
        sendMessage(gd_txt, context.bot, update.message)
    else:
        editMessage(gd_txt, sent)

def scrape_generic(link, context, update):
    sent = sendMessage('Running Scrape ...', context.bot, update.message)
    gd_txt = ""
    r = rget(link)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if any(keyword in href for keyword in ['gdtot', 'filepress', 'shortingly', 'pastetot']):
            gd_txt += f"{href}\n\n"
    if gd_txt:
        sendMessage(gd_txt, context.bot, update.message)
    else:
        sendMessage('No links found.', context.bot, update.message)

def ouo_parse(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    h = client.head(url).headers
    return h["location"]

def authIndex(user, password):
    auth = f"{user}:{password}".encode()
    return b64encode(auth).decode("utf-8")

def indexScrape(link, user, password):
    gdindex = ''
    headers = {}
    if user and password:
        headers['Authorization'] = f'Basic {authIndex(user, password)}'
    r = rget(link, headers=headers).json()
    try:
        for file in r['files']:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                gdindex += f"<b>📁 {file['name']}</b>\n{link}{quote(file['name'])}\n\n"
            else:
                gdindex += f"<code>{file['name']}</code> <i>[{get_readable_file_size(file['size'])}]</i>\n{link}{quote(file['name'])}\n\n"
    except KeyError:
        gdindex += "Invalid or No files found."
    return gdindex
