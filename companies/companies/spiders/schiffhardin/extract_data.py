from playwright.async_api import async_playwright 
from random import randint
import asyncio
from re import findall
import pickle
import traceback
import asyncio
import os 
import pandas as pd 
from parsel import Selector

# global variables and initialisation -------------------------------------------------------------------------------#
if os.path.exists('./assets/people_urls.pkl') : 
    people_urls = pickle.load(open('people_urls.pkl','rb'))
else : 
    people_urls = []


pages_number = int(input('how much tab you want : '))
headless_sign = input('enter y if you want to see the browser and n if not : ')
if headless_sign == 'y':
    headless = False
else :
    headless = True

data_list = []

# the helper functions -----------------------------------------------------------------------------------------------#

async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)
    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def run(p):
    global headless 
    global people_urls
    global pages_number
    browser = await p.firefox.launch(headless=headless)
    context = await browser.new_context()
    context.set_default_navigation_timeout(60000)   
    coros = [data_list(ch,context) for ch in 'abcdefghijklmnopqrstuvwxyz']
    await gather_with_concurrency(pages_number, *coros)


async def collect_data(url,context):
    global people_urls
    global data_list
    page = await context.new_page()
    await page.goto(url)
    selector = Selector(text=await page.content())
    await page.wait_for_timeout(15000)
    item = {
        'url': page.url,
        
    }
    await page.close()
    print('the number of urls extracted : {}'.format(len(people_urls)))
    pickle.dump(people_urls,open('./assets/people_urls.pkl','wb'))
    

async def main():
    global failed_urls
    global data_list
    async with async_playwright() as p :
        await run(p)
