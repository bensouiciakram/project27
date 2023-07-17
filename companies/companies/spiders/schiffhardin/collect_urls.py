from playwright.async_api import async_playwright 
from random import randint
import asyncio
from re import findall
import pickle
import traceback
import asyncio


# global variables and initialisation -------------------------------------------------------------------------------#
listing_template = 'https://www.schiffhardin.com/professionals/results?firstLetter={}'
people_urls = []

pages_number = int(input('how much tab you want : '))
headless_sign = input('enter y if you want to see the browser and n if not : ')
if headless_sign == 'y':
    headless = False
else :
    headless = True


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
    coros = [collect_urls(ch,context) for ch in 'abcdefghijklmnopqrstuvwxyz']
    await gather_with_concurrency(pages_number, *coros)


async def main():
    global failed_urls
    global data_list
    async with async_playwright() as p :
        await run(p)





async def collect_urls(ch,context):
    global people_urls
    global listing_template
    page = await context.new_page()
    await page.goto(listing_template.format(ch.upper()))
    await page.wait_for_timeout(15000)
    urls_handles = await page.query_selector_all('span.name a')
    people_urls += ['https://www.schiffhardin.com' +  await handle.get_attribute('href') for handle in urls_handles]
    await page.close()
    print('the number of urls extracted : {}'.format(len(people_urls)))
    pickle.dump(people_urls,open('./assets/people_urls.pkl','wb'))
    


if __name__ == '__main__' :
    try :
        asyncio.run(main())
    except : 
        print(traceback.format_exc())
        pickle.dump(people_urls,open('./assets/people_urls.pkl','wb'))


