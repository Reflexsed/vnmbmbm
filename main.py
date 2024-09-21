import asyncio
import os
import re
import requests
import logging
from telethon import TelegramClient, events
from defs import getUrl, getcards
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)

# Command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--channels', required=True, nargs='+', help='List of public channels to scrape')
args = parser.parse_args()

# API credentials and other configurations
API_ID = os.getenv('API_ID', '27201539')  # Use environment variable or fallback
API_HASH = os.getenv('API_HASH', '4655643c2d0cd4891daacb697ef81108')
SEND_CHAT = -1002232956390  # Channel to upload scraped data
PRIVATE_CHANNEL = -1001833380321  # Your private channel ID
USERNAME = 'NetWraith'  # Your username here (without @)

client = TelegramClient('session', API_ID, API_HASH)
ccs = []

# Load cards from file
try:
    with open('cards.txt', 'r') as r:
        temp_cards = r.read().splitlines()
except FileNotFoundError:
    temp_cards = []

for x in temp_cards:
    car = getcards(x)
    if car:
        ccs.append(car[0])

@client.on(events.NewMessage(chats=args.channels + [PRIVATE_CHANNEL], func=lambda x: getattr(x, 'text')))
async def my_event_handler(m):
    try:
        text = m.text
        urls = getUrl(text)
        if urls:
            text = requests.get(urls[0]).text
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return

    cards = getcards(text)
    if not cards:
        return

    cc, mes, ano, cvv = cards
    if cc in ccs:
        return

    try:
        bin_response = requests.get(f'https://adyen-enc-and-bin-info.herokuapp.com/bin/{cc[:6]}')
        bin_response.raise_for_status()  # Check for HTTP errors
        bin_json = bin_response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching BIN info: {e}")
        return

    if len(ano) == 2:
        ano = '20' + ano

    fullinfo = f"{cc}|{mes}|{ano}|{cvv}"
    text_to_send = f"""
    <b>CARD :</b> <code>{cc}|{mes}|{ano}|{cvv}</code>\n
    <b>INFO:</b> <i>{bin_json['vendor']} - {bin_json['type']} - {bin_json['level']}</i>\n
    <b>BIN:</b> <a href="https://t.me/ScrapperScar"><code>{bin_json['bin']}</code></a>\n
    <b>BANK:</b> {bin_json['bank']} \n
    <b>COUNTRY:</b> {bin_json['country_iso']} - {bin_json['flag']}\n
    <b>CREDITED TO:</b> @{USERNAME}\n
    ╔══════════ Extra ═════════╗
    ╠ <code>{cc[:12]}xxxx|{mes}|{ano}|xxx</code>
    ╚═══════════════════════╝

    \n
    """

    logging.info(f'Saving card info: {fullinfo}')
    with open('cards.txt', 'a') as w:
        w.write(fullinfo + '\n')

    await client.send_message(SEND_CHAT, text_to_send, parse_mode='html')

# Start the client
client.start()
client.run_until_disconnected()
