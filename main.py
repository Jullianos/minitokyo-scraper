import os
import shutil
from datetime import datetime

from get_images import scrape_images_from_minitokyo, get_last_index_from_minitokyo_json, MAIN_MINITOKYO_JSON_FILEPATH

version_name = 'Yandere_Scraper v1.0'

# Make a backup of the main file before doing anything
if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):
    shutil.copyfile(MAIN_MINITOKYO_JSON_FILEPATH, MAIN_MINITOKYO_JSON_FILEPATH[:-5] + '-MAIN-BACKUP-' + str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + '.json')

while True:
    print('\nWelcome to ' + version_name + ',\nType "Help" for commands\nLast index of main file is: ' +
          str(get_last_index_from_minitokyo_json(MAIN_MINITOKYO_JSON_FILEPATH)))

    user_input = input('Command: ')

    if user_input == 'Help':
        print('Command: "Initial" starts scraping from the beginning.')
        print('Command: "Continue" continues scraping from the last downloaded index.')

    if user_input == 'Initial':
        print('Command: "Initial" acknowledged.')
        scrape_images_from_minitokyo('Initial')

    if user_input == 'Continue':
        print('Command: "Continue" acknowledged.')
        scrape_images_from_minitokyo('Continue')
