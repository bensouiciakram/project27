import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
from scrapy.selector import Selector


class SkaddenSpider(scrapy.Spider):
    name = 'schiffhardin'
    allowed_domains = ['schiffhardin.com']
    start_urls = ['https://www.schiffhardin.com/professionals/results?keyword=']


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            stealth_sync(page)
            page.goto(self.start_urls[0],timeout=60000)
            page.wait_for_timeout(10000)
            page.wait_for_selector('a.view-all')
            page.click('a.view-all')
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
            page.wait_for_selector('//span[contains(text(),"View All")]')
            page.click('//span[contains(text(),"View All")]')
            for _ in range(10):
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
                page.wait_for_timeout(5000)
            urls = [handle.get_attribute('href') for handle in page.query_selector_all('span.name a')]
            self.start_urls = ['https://www.schiffhardin.com' + url for url in urls]


    def parse(self,response):
        url = response.url
        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            stealth_sync(page)
            page.goto(response.url)
            page.wait_for_selector('//header//h1')
            page.wait_for_timeout(15000)
            response = Selector(text = page.content())
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
        fullname_list = response.xpath('string(//header//h1)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.print-position::text')
        loader.add_css('email','span.email-holder a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try : 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError :
            pass
        loader.add_value('image','https://www.schiffhardin.com'+response.css('div.bio-photo img::attr(src)').get())
        loader.add_xpath('bio','string(//div[@id="Overview"])')
        loader.add_value('firm_bio','https://www.schiffhardin.com/about-us')
        loader.add_css('office','span.city a::text')
        yield loader.load_item()


    def get_total(self,response):
        pass 


    def get_law_school(self,educations_list):
        year = education = ''
        for edu in educations_list : 
            if 'law' in edu.lower() : 
                education = edu
                try :
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    pass
                return education,year


    def get_undergraduate_school(self,educations_list):
        year = education = ''
        for edu in educations_list : 
            if not 'law' in edu.lower() : 
                education = edu
                try : 
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    pass
                return education,year


            