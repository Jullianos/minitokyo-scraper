from bs4 import BeautifulSoup
from datetime import datetime
from lxml import html
from collections import defaultdict
import requests
import time
import json
import os
import re
import shutil
import pprint


MINITOKYO_URL = 'http://gallery.minitokyo.net/view/'
MINITOKYO_DOWNLOAD_LOCATION = 'images/minitokyo/'
MAIN_MINITOKYO_JSON_FILEPATH = 'json/minitokyo/minitokyo.json'
MINITOKYO_DOWNLOAD_URL = 'http://gallery.minitokyo.net'

USERNAME = "Harlusak"
PASSWORD = "ndbaturt"

LOGIN_URL = "http://my.minitokyo.net/login"


def download_image(url, name):
    while True:
        try:
            try:
                r = requests.get(url, allow_redirects=True)
                open(name, 'wb').write(r.content)
                break
            except ConnectionAbortedError:
                print('<-Connection Error (Image)-> reconnecting...')
                time.sleep(5)
        except requests.ConnectionError:
            print('<-Connection Error (Image)-> reconnecting...')
            time.sleep(5)


def get_last_index_from_minitokyo_json(filepath):

    # get the last index
    if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):
        with open(filepath, 'r') as main_file:
            data = json.loads(main_file.read())

            last = 0
            for key, value in data.items():
                if int(key) > last:
                    last = int(key)

        return last

    print('No main json file.')

    return None


def scrape_images_from_minitokyo(Type):

    if Type == 'Continue':
        # get the last index
        # continue to scrape from the last index
        if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):
            x = get_last_index_from_minitokyo_json(MAIN_MINITOKYO_JSON_FILEPATH) + 1
        else:
            print('\nCannot Continue, there is no main json file.\n')
            return None

    elif Type == 'Initial':

        # if there is already a main file copy it and rename it, and remove the main file
        if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):
            shutil.copyfile(MAIN_MINITOKYO_JSON_FILEPATH, MAIN_MINITOKYO_JSON_FILEPATH +
                            str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + '.json')

            os.remove(MAIN_MINITOKYO_JSON_FILEPATH)

            with open(MAIN_MINITOKYO_JSON_FILEPATH, 'w') as new_file:
                new_file.write('{}')

                print('Main file for initial scrape created: "minitokyo.json"')
        else:
            with open(MAIN_MINITOKYO_JSON_FILEPATH, 'w') as new_file:
                new_file.write('{}')

                print('Main file for initial scrape created: "minitokyo.json"')

        x = 0

    else:
        return None

    if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):

        # log in into minitokyo.net
        session_requests = requests.session()

        # Get login csrf token
        # result = session_requests.get(LOGIN_URL)
        # tree = html.fromstring(result.text)
        # authenticity_token = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']/@value")))[0]

        # Create payload
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            # "csrfmiddlewaretoken": authenticity_token
        }

        # Perform login
        result = session_requests.post(LOGIN_URL, data=payload, headers=dict(referer=LOGIN_URL))
        not_found = []

        while True:
            while True:
                try:
                    try:
                        # page = requests.get(MINITOKYO_URL + str(x), headers={'User-agent': 'Mr.163211'})
                        page = session_requests.get(MINITOKYO_URL + str(x), headers=dict(referer=MINITOKYO_URL + str(x)))

                        # print('page: ' + str(page))
                        # print('result: ' + str(result))

                        break
                    except ConnectionAbortedError:
                        print('<-Connection Error (Image)-> reconnecting...')
                        time.sleep(5)
                except requests.ConnectionError:
                    print('<-Connection Error-> reconnecting...')
                    time.sleep(5)

            if page.status_code == 404:
                print(str(x) + ' doesnt exist.')
                x += 1

            elif page.status_code == 410:
                print(str(x) + ' was removed.')
                x += 1

            elif page.status_code == 500:
                time.sleep(5)

            elif page.status_code == 200:

                soup = BeautifulSoup(page.content, 'html.parser')

                # get the image id and initialize the dictionary
                stats = {'id': x}

                # Get the image url and download it in the highest resolution
                download_url = MINITOKYO_DOWNLOAD_URL + str(soup.find('div', id='preview').find_all('a')[0]['href'])
                download_page = session_requests.get(download_url, headers=dict(referer=download_url))
                download_soup = BeautifulSoup(download_page.content, 'html.parser')

                image_url = download_soup.find_all('img')[0]['src']

                if image_url is not None:
                    image_name = MINITOKYO_DOWNLOAD_LOCATION + str(x) + image_url[-4:]

                    download_image(image_url, image_name)
                    stats['image_src'] = image_url
                else:
                    print('Image was not found!')
                    not_found.append(x)

                # Get the info about the image
                desc_list = soup.find('div', id='menu').find_all('dl')[0]
                stats['type'] = desc_list.find('dt', text='Type').next_sibling.text
                stats['resolution'] = desc_list.find('dt', text='Dimensions').next_sibling.text
                stats['views'] = int(desc_list.find('dt', text='Views').next_sibling.text.replace(',', ''))
                stats['downloads'] = int(desc_list.find('dt', text='Downloads').next_sibling.text.replace(',', ''))
                stats['comments'] = int(desc_list.find('dt', text='Comments').next_sibling.text.replace(',', ''))
                stats['favorites'] = int(desc_list.find('dt', text='Favorites').next_sibling.text.replace(',', ''))

                # Get the image tags
                try:
                    tags_ul = soup.find('div', id='tag-list').find('ul').find_all('li')
                    special_tags = defaultdict(list)
                    tags = []

                    for li in tags_ul:
                        em = li.find('em')
                        if em is not None:
                            tag_type = li.find('b').text

                            special_tags[tag_type].append(em.find('a').text)
                        else:
                            tags.append(li.find('a').text)

                    stats['special_tags'] = special_tags
                    stats['tags'] = tags
                except AttributeError:
                    all_p = soup.find_all('p', attrs={'class': 'empty'})

                    for p in all_p:
                        if 'No tags' in p.text:
                            print('This image has no tags!')
                            stats['special_tags'] = None
                            stats['tags'] = None

                # If there is a main file work with it
                if os.path.isfile(MAIN_MINITOKYO_JSON_FILEPATH):
                    with open(MAIN_MINITOKYO_JSON_FILEPATH, 'r') as json_file:
                        yandere_info = json.loads(json_file.read())
                        yandere_info[x] = stats

                        with open(MAIN_MINITOKYO_JSON_FILEPATH, 'w') as updated_json_file:
                            updated_json_file.write(json.dumps(yandere_info))

                print(str(x) + ' has been downloaded.\tNot found: ' + str(not_found))

                # smart increment for the next index (skipping the 404 pages, because the website provides a "next"
                # button)
                x += 1

            else:

                print('[DEAD]Status:' + str(page.status_code))
                break
    else:
        print('There is no main file.')
