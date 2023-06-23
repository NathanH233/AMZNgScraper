from cmath import e
import math
import requests
import random as rand
import re


import time
from bs4 import BeautifulSoup

# Start the timer
start_time = time.time()

session = requests.Session()

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'en-US,en;q=0.5',
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'connection': 'close',
    'referer': 'https://www.amazon.com/'
}

session.headers = headers

# These ASIN's will not be scraped since the category tends to have no FAQ data
exclusion_list = ["Amazon Explore",
                  "Apps & Games",
                  "Audible Books & Originals",
                  "Books",
                  "CDs & Vinyl",
                  "Digital Educational Resources",
                  "Digital Music",
                  "Gift Cards",
                  "Kindle Store",
                  "Magazine Subscriptions",
                  "Movies & TV"]

# Strings consistent with an error retrieving a webpage
error_str = [
    "<html><body><p>Request was throttled. Please wait a moment and refresh the page</p></body></html>"
]


def get_good_soup(url, max_retries=5):
    for _ in range(max_retries):
        url_get = session.get(url)
        url_soup = BeautifulSoup(url_get.content, 'lxml')
        if url_soup is not None and str(url_soup) not in error_str:
            return url_soup
        time.sleep(rand.randrange(start=1, stop=3))
    raise IOError("Failed to retrieve good soup for following URL:\n{0}\n"\
                  "Here's the soup we got instead:\n{1}".format(url, url_soup))


def get_sub_department_links(soup):
    sub_list = set()
    try:
        div_list = soup.find('body')\
                    .find('div', {'id': 'a-page'})\
                    .find('div', {'id': 'zg'})\
                    .find('div', {'class': 'a-fixed-left-flipped-grid'})\
                    .find('div', {'class': 'a-fixed-left-grid-inner'})\
                    .find('div', {'id': 'zg-left-col'})\
                    .find('div')\
                    .find('div')\
                    .find_all('div')[1]\
                    .find('div', {'role': 'group'})\
                    .find_all('div')
        for div in div_list:
            text = div.find('a').contents[0]
            link = div.find('a').get('href')
            if text in exclusion_list:
                continue
            sub_list.add('https://www.amazon.com' + link)
            print(link)
        return sub_list
    except AttributeError as e:
        print("This department has no sub-departments")
        return None


def get_department_links(soup):
    '''
    This function compiles a list of links to web pages we need to
    scrape for product info.
    '''
    dep_list = []
    div_list = soup.find('body')\
                   .find('div', {'id': 'a-page'})\
                   .find('div', {'id': 'zg'})\
                   .find('div', {'id': 'zg_colmask'})\
                   .find('div', {'id': 'zg_colleft'})\
                   .find('div', {'id': 'zg_col1wrap'})\
                   .find('div', {'id': 'zg_col1'})\
                   .find('div', {'id': 'zg_left_colmask'})\
                   .find('div', {'id': 'zg_left_colleft'})\
                   .find('div', {'id': 'zg_left_col2'})\
                   .find('div')\
                   .find('div')\
                   .find('div', {'role': 'group'})\
                   .find_all('div')
    for div in div_list:
        text = div.find('a').contents[0]
        link = 'https://www.amazon.com' + div.find('a').get('href')
        if text in exclusion_list:
            continue
        dep_list.append(link)
        print(link)
        sub_soup = get_good_soup(link)
        sub_list = get_sub_department_links(sub_soup)
        if sub_list is not None:
            dep_list.append(link)
    return dep_list


def get_asins(dept_url):
    dept_soup = get_good_soup(dept_url)
    try:
        item_list = dept_soup.find('body')\
            .find('div', {'id': 'a-page'})\
            .find('div', {'id': 'zg'})\
            .find('div', {'class': 'a-fixed-left-flipped-grid'})\
            .find('div', {'class': 'a-fixed-left-grid-inner'})\
            .find('div', {'id': 'zg-right-col'})\
            .find('div')\
            .find('div')\
            .find('div', {'data-a-card-type': 'basic'})\
            .find_all('div')[0]\
            .get('data-client-recs-list')
        return re.findall(r'\b[A-Z0-9]{10}\b', item_list)
    except AttributeError as e:
        print(dept_url)
        raise


def scrape_asins():
    try:
        # Getting soup object for best seller page
        best_seller_url = "https://www.amazon.com/Best-Sellers/zgbs/"
        best_seller_soup = get_good_soup(best_seller_url)

        # Go through each department and filter excluded categories
        asin_list = set()
        departments = get_department_links(best_seller_soup)
        for department_url in departments:
            # Going through each listed item box in each department page to get link to item page
            for i in range(2):
                if i == 2:
                    department_url = department_url + "&pg=2"
                asin_list.update(get_asins(department_url))
        return asin_list
    except IOError as e:
        print(e)
    except AttributeError as e:
        print(e)


if __name__ == '__main__':
    asins = scrape_asins()
    with open("asins.txt", 'w') as file:
        file.write(str(asins).replace(" ", "\n"))

# Calculate the elapsed time
elapsed_mins = math.floor((time.time() - start_time) / 60.)
elapsed_secs = (time.time() - start_time) % 60
print("Elapsed time: {0} minutes and {1} seconds".format(
    elapsed_mins, elapsed_secs))
