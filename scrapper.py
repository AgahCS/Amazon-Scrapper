

import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
import os.path
import sys

no_pages = 2

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'close'
}


column_names = ['EAN', 'ASIN', 'Best Sellers Rank', 'Total ratings']
df = pd.DataFrame(columns=column_names)

with open('config.json') as f:
    data = json.load(f)

input_file = data["file_details"].get("input_file_name")
input_df = pd.read_excel(input_file)


# parse html to get the url
def parse_content(r):
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    url = ''
    for d in soup.findAll('div', attrs={'class': 's-main-slot s-result-list s-search-results sg-row'}):
        for k in d.findAll('div', attrs={'class': 'sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col sg-col-4-of-20'}):
            asin = k['data-asin']
            for a in k.find_all('a', attrs={'class': 'a-link-normal a-text-normal'}, href=True):
                url = 'https://www.amazon.com'+a['href']
    return asin, url


# returns product url
def get_url(ean):
    try:
        r = requests.get('https://www.amazon.com/s?k='+str(ean)+'&ref=nb_sb_noss' +
                         str(2)+'?ie=UTF8&pg='+str(2), headers=headers)  # , proxies=proxies)
        return parse_content(r)
    except:
        try:
            r = requests.get('https://www.amazon.com/s?k='+'0'+str(ean)+'&ref=nb_sb_noss' +
                             str(2)+'?ie=UTF8&pg='+str(2), headers=headers)  # , proxies=proxies)
            return parse_content(r)
        except:
            pass


# fetches product data
def get_data(url):
    r = requests.get(url+str(2)+'?ie=UTF8&pg='+str(2),
                     headers=headers)  # , proxies=proxies)
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    for d in soup.findAll('div', attrs={'id': 'detailBulletsWrapper_feature_div'}):
        ranks = []
        for l in d.findAll('span', attrs={'class': 'a-list-item'}):
            if '#' in l.text:
                for word in l:
                    text = str(word).replace('\n', '').replace(
                        '\r', '')  # removes all line change
                    # removes html tags
                    text = re.sub('<[^<>]+>', '', text)
                    ranks.append(str(text))
        ranks = ''.join(ranks)  # removes all text inside ()
        ranks = re.sub(r'\([^)]*\)', '', ranks)
        ranks = ranks.replace('Best Sellers Rank:', '')
        ranks = ranks.replace('&amp;', '&')
    for d in soup.find('span', attrs={'id': 'acrCustomerReviewText'}):
        rating = d.replace('ratings', '')
    return ranks, rating

val = 1
if os.path.isfile('output.xlsx'):
    val = input(
        "This will overwrite output.xlsx\nEnter 0 to abort, enter any other key to continue ")

if val != '0':
    for index, row in input_df.iterrows():
        try:
            new_df = {}
            print('Fetching data for : ' + str(row['EAN']))
            asin, url = get_url(row['EAN'])
            ranks, rating = get_data(url)
            new_df[column_names[0]] = row['EAN']
            new_df[column_names[1]] = asin
            new_df[column_names[2]] = ranks
            new_df[column_names[3]] = rating
            df = df.append(new_df, ignore_index=True)
        except Exception as e:
            print("Cannot find data for EAN: " + str(row['EAN']))

    print(df)
    df.to_excel('output.xlsx')
