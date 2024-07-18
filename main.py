import os
import platform
import signal
import requests
import subprocess
from gpiozero import Button

## Variables

base_url = 'https://api.scryfall.com/'

printer_mac = 'AA:BB:CC:DD:EE:FF'
temp_image_path = 'image.png'

button_pin = 7

last_card = None

## Functions

def printImage(printerMac, imagePath):
    venv_python = 'catprinter/venv/bin/python'
    args = [venv_python, 'catprinter/print.py', '-d', printerMac, imagePath]
    subprocess.run(args)

def printCard(card):
    if "image_uris" in card:
        print(card['image_uris']['normal'])
        r = requests.get(card['image_uris']['normal'])
        with open(temp_image_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        printImage(printer_mac, temp_image_path)
    else:
        if "card_faces" in card:
            for face in card['card_faces']:
                print(face['image_uris']['normal'])
                r = requests.get(card['image_uris']['normal'])
                with open(temp_image_path, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                printImage(printer_mac, temp_image_path)

def printRandomCard():
    params = dict(
        q = '-t:land'
    )
    resp = requests.get(url=base_url + 'cards/random')
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

## Script

button = Button(button_pin, hold_time=3)
button.when_pressed = printRandomCard
button.when_held = printRelatedCards

match platform.system():
    case 'Linux':
        signal.pause()   
    case 'Windows':
        os.system('pause')
