import json
import cloudscraper
import concurrent.futures
import requests
from copy import deepcopy
from re import match as rematch, sub as resub, compile as recompile
from asyncio import sleep as asleep
from urllib.parse import quote
from requests import get as rget, post as rpost
from bs4 import BeautifulSoup, NavigableString, Tag
from base64 import b64decode, b64encode
from telegram import Message
from telegram.ext import CommandHandler
from bot import LOGGER, dispatcher, config_dict, OWNER_ID
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.ext_utils.bot_utils import is_paid, is_sudo, get_readable_file_size
from bot.helper.mirror_utils.download_utils.direct_link_generator import rock, ouo

next_page = False
next_page_token = ""
post_id = ""
data_dict = {}
main_dict = {}
DDL_REGEX = recompile(r"DDL\(([^),]+)\, (([^),]+)), (([^),]+)), (([^),]+))\)")
POST_ID_REGEX = recompile(r'"postId":"(\d+)"')

def scrapper(update, context):
    user_id_ = update.message.from_user.id
    if config_dict['PAID_SERVICE'] is True:
        if user_id_ != OWNER_ID and not is_sudo(user_id_) and not is_paid(user_id_):
            sendMessage("Buy Paid Service to Use this Scrape Feature.", context.bot, update.message)
            return

    message: Message = update.effective_message
    link = None
    if message.reply_to_message:
        link = message.reply_to_message.text
    else:
        userindex, passindex = 'none', 'none'
        link = message.text.split('\n')
        if len(link) == 3:
            userindex = link[1]
            passindex = link[2]
        link = link[0].split(' ', 1)
        if len(link) == 2:
            link = link[1]
        else:
            help_msg = "<b>Send link after command:</b>"
            help_msg += f"\n<code>/{BotCommands.ScrapeCommand[0]} {{link}}</code>\n"
            help_msg += "\n<b>By Replying to Message (Including Link):</b>"
            help_msg += f"\n<code>/{BotCommands.ScrapeCommand[0]} {{message}}</code>"
            return sendMessage(help_msg, context.bot, update.message)
    
    try:
        link = rematch(r"^(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", link)[0]
    except TypeError:
        return sendMessage('Not a Valid Link.', context.bot, update)

    links = []
    if "sharespark" in link:
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
        if gd_txt != "":
            sendMessage(gd_txt, context.bot, update.message)
    elif "tamilmv" in link:
        sent = sendMessage('Running Scrape...', context.bot, update.message)
        cget = cloudscraper.create_scraper().request
        resp = cget("GET", link)
        soup = BeautifulSoup(resp.text, "html.parser")
        mag = soup.select('a[href^="magnet:?xt=urn:btih:"]')
        tor = soup.select('a[data-fileext="torrent"]')
        parse_data = f"<b><u>{soup.title.string}</u></b>"
        for no, (t, m) in enumerate(zip(tor, mag), start=1):
            filename = resub(r"www\S+|\- |\.torrent", "", t.string)
            parse_data += (f"""
            
{no}. <code>{filename}</code>
┖ <b>Links :</b> <a href="https://t.me/share/url?url={m['href'].split('&')[0]}"><b>Magnet </b>🧲</a>  | <a href="{t['href']}"><b>Torrent 🌐</b></a>""")
        editMessage(parse_data, sent)

    elif "teluguflix" in link:
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
            asleep(1.5)
            if len(gd_txt) > 4000:
                sent = sendMessage("<i>Running More Scrape ...</i>", context.bot, update.message)
                gd_txt = ""
    elif "cinevood" in link:
       sent = sendMessage('Running Scrape ...', context.bot, update.message)
       soup = BeautifulSoup(r.text, "html.parser")
       titles = soup.select("h6")
       links_by_title = {}

    # Extract the post title from the webpage's title
       post_title = soup.title.string.strip()

       for title in titles:
           title_text = title.text.strip()
           gdtot_links = title.find_next("a", href=lambda href: "gdtot" in href.lower())
           multiup_links = title.find_next("a", href=lambda href: "multiup" in href.lower())
           filepress_links = title.find_next("a", href=lambda href: "filepress" in href.lower())
           gdflix_links = title.find_next("a", href=lambda href: "gdflix" in href.lower())
           kolop_links = title.find_next("a", href=lambda href: "kolop" in href.lower())
           zipylink_links = title.find_next("a", href=lambda href: "zipylink" in href.lower())

           links = []
           if gdtot_links:
              links.append(f'<a href="{gdtot_links["href"]}" style="text-decoration:none;"><b>GDToT</b></a>')
           if multiup_links:
            links.append(f'<a href="{multiup_links["href"]}" style="text-decoration:none;"><b>MultiUp</b></a>')
           if filepress_links:
            links.append(f'<a href="{filepress_links["href"]}" style="text-decoration:none;"><b>FilePress</b></a>')
          if gdflix_links:
            links.append(f'<a href="{gdflix_links["href"]}" style="text-decoration:none;"><b>GDFlix</b></a>')
          if kolop_links:
            links.append(f'<a href="{kolop_links["href"]}" style="text-decoration:none;"><b>Kolop</b></a>')
          if zipylink_links:
            links.append(f'<a href="{zipylink_links["href"]}" style="text-decoration:none;"><b>ZipyLink</b></a>')
          if links:
            links_by_title[title_text] = links

       prsd = f"<b>🔖 Title:</b> {post_title}\n"
       for title, links in links_by_title.items():
           prsd += f"\n┏<b>🏷️ Name:</b> <code>{title}</code>\n"
           prsd += "┗<b>🔗 Links:</b> " + " | ".join(links) + "\n"
            sendMessage(prsd, context.bot, update.message)
    elif "atishmkv" in link:
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
        if prsd != "":
            sendMessage(prsd, context.bot, update.message)
    elif "taemovies" in link:
        sent = sendMessage('Running Scrape ...', context.bot, update.message)
        gd_txt, no = "", 0
        r = rget(link)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="shortingly"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        editMessage(gd_txt, sent)
        for a in links:
            glink = rock(a["href"])
            t = rget(glink)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.select('meta[property^="og:description"]')
            no += 1
            gd_txt += f"{no}. {(title[0]['content']).replace('Download ', '')}\n{glink}\n\n"
            editMessage(gd_txt, sent)
            if len(gd_txt) > 4000:
                sent = sendMessage("<i>Running More Scrape ...</i>", context.bot, update.message)
                gd_txt = ""
    elif "toonworld4all" in link:
        sent = sendMessage('Running Scrape ...', context.bot, update.message)
        gd_txt, no = "", 0
        client = requests.session()
        r = client.get(link).text
        soup = BeautifulSoup(r, "html.parser")
        for a in soup.find_all("a"):
            c = a.get("href")
            if "redirect/main.php?" in c:
                download = rget(c, stream=True, allow_redirects=False)
                link = download.headers["location"]
                g = rock(link)
                if "gdtot" in g:
                    t = client.get(g).text
                    soupt = BeautifulSoup(t, "html.parser")
                    title = soupt.title
                    no += 1
                    gd_txt += f"{no}. {title.get_text().replace('Download ', '')}\n{g}\n\n"
                    editMessage(gd_txt, sent)
                    if len(gd_txt) > 4000:
                        sent = sendMessage("<i>Running More Scrape ...</i>", context.bot, update.message)
                        gd_txt = ""
    elif "katdrive" in link:
        sent = sendMessage("Running Scrape ...", context.bot, update.message)
        res = cloudscraper.create_scraper(interpreter="nodejs").get(link)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a")
        file = f"\n\n{len(links)} links found."
        prsd = ""
        editMessage(file, sent)
        for a in links:
            prsd += f"\n<a href='{a['href']}'>{a['href']}</a>"
            editMessage(prsd, sent)
            if len(prsd) > 4000:
                sendMessage(prsd, context.bot, update.message)
                prsd = ""
        if prsd != "":
            sendMessage(prsd, context.bot, update.message)
    elif "upfile" in link:
        sent = sendMessage("Running Scrape ...", context.bot, update.message)
        res = cloudscraper.create_scraper(interpreter="nodejs").get(link)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a")
        file = f"\n\n{len(links)} links found."
        prsd = ""
        editMessage(file, sent)
        for a in links:
            prsd += f"\n<a href='{a['href']}'>{a['href']}</a>"
            editMessage(prsd, sent)
            if len(prsd) > 4000:
                sendMessage(prsd, context.bot, update.message)
                prsd = ""
        if prsd != "":
            sendMessage(prsd, context.bot, update.message)
    else:
        try:
            scraper = cloudscraper.create_scraper()
            url = quote(link)
            api = f"https://2giga.link/api/get-dl-link/?link={url}&key=7d5e17e8cc2e2e6d482bcd0bbf95ab0b"
            res = scraper.get(api).json()
            if res['status'] == 'success':
                sendMessage(f"Successfully Scrapped!\n\n{res['download_link']}", context.bot, update.message)
            else:
                sendMessage('Failed to Scrap Link!', context.bot, update.message)
        except Exception as e:
            LOGGER.error(e)
            sendMessage(f'Something went wrong: {e}', context.bot, update.message)

scrapper_handler = CommandHandler(BotCommands.ScrapeCommand, scrapper, filters=CustomFilters.owner_filter | CustomFilters.authorized_user)
dispatcher.add_handler(scrapper_handler)
