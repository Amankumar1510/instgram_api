import os
from instagrapi import Client
import ssl

from lxml.html import fromstring
import requests
from itertools import cycle
import traceback

# def get_proxies():
#     url = 'https://free-proxy-list.net/'
#     response = requests.get(url)
#     parser = fromstring(response.text)
#     proxies = set()
#     for i in parser.xpath('//tbody/tr')[:10]:
#         if i.xpath('.//td[7][contains(text(),"yes")]'):
#             proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
#             proxies.add(proxy)
#             print(f"Added proxy: {proxy}")
#     return proxies

proxies = set()

def get_proxies():
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    parser = fromstring(response.content)
    print(f"Respons is {response}")

        # Select table rows within tbody
    for row in parser.xpath('//table//tbody/tr'):
        # Extract all cell values safely
        cells = [td.text_content().strip() for td in row.xpath('.//td')]
        
        if len(cells) >= 7:
            ip = cells[0]
            port = cells[1]
            https = cells[6].lower()

            # Only pick proxies that support HTTPS
            if "yes" in https:
                proxy = f"{ip}:{port}"
                proxies.add(proxy)

    print("Fetched proxies:")
    for p in proxies:
        print(p)
    return proxies

def find_working_proxy(proxies):
    proxy_pool = cycle(proxies)

    url = 'https://httpbin.org/ip'
    for i in range(len(proxies)):
        #Get a proxy from the pool
        proxy = next(proxy_pool)
        print("Request #%d"%i)
        try:
            response = requests.get(url,proxies={"http": proxy, "https": proxy}, timeout=10)
            if response.status_code == 200:
                print("working proxy found")
                print(response.json())
                working_proxy = proxy
                break
        except:
            #Most free proxies will often get connection errors. You will have to retry the entire request using another proxy to work. 
            #You can just skip retries as its beyond the scope of this tutorial and you are only downloading a single url 
            print("Skipping. Connection error")
    return working_proxy
   
#If you are copy pasting proxy ips, put in the list below
#proxies = ['121.129.127.209:80', '124.41.215.238:45169', '185.93.3.123:8080', '194.182.64.67:3128', '106.0.38.174:8080', '163.172.175.210:3128', '13.92.196.150:8080']
# proxies.clear()
# proxies = get_proxies()
# print(f"and proxies are {proxies}")
# proxy_pool = cycle(proxies)

# url = 'https://httpbin.org/ip'
# for i in range(len(proxies)):
#     #Get a proxy from the pool
#     proxy = next(proxy_pool)
#     print("Request #%d"%i)
#     try:
#         response = requests.get(url,proxies={"http": proxy, "https": proxy}, timeout=10)
#         if response.status_code == 200:
#             print("working proxy found")
#             print(response.json())
#             working_proxy = proxy
#             break
#     except:
#         #Most free proxies will often get connection errors. You will have to retry the entire request using another proxy to work. 
#         #You can just skip retries as its beyond the scope of this tutorial and you are only downloading a single url 
#         print("Skipping. Connection error")































print("Python's default SSL/TLS protocol version:", ssl.PROTOCOL_TLS_CLIENT)
print("Supported protocol versions:", ssl.OPENSSL_VERSION)

# Get credentials from environment variables
# ACCOUNT_USERNAME = os.environ.get("INSTA_USERNAME")
# ACCOUNT_PASSWORD = os.environ.get("INSTA_PASSWORD")
ACCOUNT_USERNAME = "_.aman._kumar._"
ACCOUNT_PASSWORD = "amanrandompwd"

if not ACCOUNT_USERNAME or not ACCOUNT_PASSWORD:
    print("Error: Please set the INSTA_USERNAME and INSTA_PASSWORD environment variables.")
else:
    cl = Client()
    try:
        proxies.clear()
        proxies = get_proxies()
        working_proxy = find_working_proxy(proxies)
        print(f"Working proxy is {working_proxy}")
        proxy = working_proxy

        cl.set_proxy(proxy)
        # cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)
        # print("Login successful!")
        
        user_id = cl.user_id_from_username("hollsghoul")
        followers = cl.user_followers(user_id)
        # followers = cl.user_followers("nazilx", amount=50)
        # print(f"Followers: {followers}")
        # print(f"All the followers: {list(followers.values())[0]}")

        # user_id = cl.user_id_from_username(ACCOUNT_USERNAME)
        # medias = cl.user_medias(user_id, 20)

        # print(f"Found {len(medias)} medias for user {ACCOUNT_USERNAME}:")
        # for i, media in enumerate(medias):
        #     print(f"  {i+1}. Media PK: {media.pk}, Type: {media.media_type}, URL: {media.thumbnail_url}")
        
        # target_id = cl.user_id_from_username("rvcjinsta")
        # posts = cl.user_medias(target_id, amount=10)
        # for media in posts:
        #     # download photos to the current folder
        #     cl.photo_download(media.pk, filename=f"post_{media.pk}.jpg")

    except Exception as e:
        print(f"An error occurred: {e}")