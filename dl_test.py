from playwright.sync_api import sync_playwright
from time import sleep 

data = set()

def get_data(response):
    if '?sitecoreItemUri' in response.url :
        global data
        print('\n\n' + str(len(response.json()['results'])) + '\n\n')
        people_urls = {individual['ClickUri'] for individual in response.json()['results']}
        print(people_urls)
        data.union(people_urls)
        print(data)
        return response.json()    


def run(p):
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.on('response',get_data)
    page.goto('https://www.dlapiper.com/en/us/people/#sort=relevancy')
    page.click('//a[contains(text(),"100")]')
    page.wait_for_timeout(5000)
    total_pages = get_total(page)//100
    for page_id in range(1,4):#total_pages + 1) :
        sleep(3)
        page.goto('https://www.dlapiper.com/en/us/people/#first={}&sort=relevancy'.format(100*(page_id - 1)))
        page.wait_for_timeout(3000)
        print(' {} urls collected '.format(len(data)))
        



def get_total(page):
    return int(page.query_selector('//span[@class="CoveoQuerySummary"]//span[3]').inner_text().replace(',',''))

with sync_playwright() as playwright :
    run(playwright)
    breakpoint()
breakpoint()



