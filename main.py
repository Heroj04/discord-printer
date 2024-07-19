import asyncio
import os
import platform
import signal
import requests
from gpiozero import Button
from dotenv import load_dotenv
from PIL import Image

from catprinter.catprinter.cmds import PRINT_WIDTH, cmds_print_img
from catprinter.catprinter.ble import run_ble

## Variables

load_dotenv()

base_url = os.getenv('BASE_URL')
query = os.getenv('QUERY')

printer_mac = os.getenv('PRINTER_MAC')
temp_image_path = os.getenv('TEMP_IMAGE_PATH')

button_pin = os.getenv('BUTTON_PIN')

last_card = None

## Functions

def printImage(printerMac, imagePath):
    image = loadImage(imagePath)
    data = cmds_print_img(image)
    asyncio.run(run_ble(data, printerMac))
    
def downloadImage(uri):
    r = requests.get(uri)
    with open(temp_image_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

def printCard(card):
    if "image_uris" in card:
        downloadImage(card['image_uris']['normal'])
        printImage(printer_mac, temp_image_path)
    else:
        if "card_faces" in card:
            for face in card['card_faces']:
                downloadImage(face['image_uris']['normal'])
                printImage(printer_mac, temp_image_path)

def printRandomCard():
    params = dict(
        q = query
    )
    resp = requests.get(url=base_url + 'cards/random', params=params)
    last_card = resp.json()
    printCard(last_card)

def printRelatedCards():
    if last_card is None:
        return

    for part in last_card['all_parts']:
        if part['name'] != last_card['name']:
            resp = requests.get(url=part['uri'])
            cardPart = resp.json()
            printCard(cardPart)
            
def loadImage(path):
    im = Image.open(path).convert('L')
    width, height = im.size
    factor = PRINT_WIDTH / width
    resized = im.resize((PRINT_WIDTH, int(height * factor)))
    resized = resized.convert('1')
    return resized

## Script

button = Button(button_pin, hold_time=3)
button.when_pressed = printRandomCard
button.when_held = printRelatedCards

#printRandomCard()

match platform.system():
    case 'Linux':
        signal.pause()   
    case 'Windows':
        os.system('pause')
