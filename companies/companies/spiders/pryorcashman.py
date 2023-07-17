import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
import re 
from scrapy import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'pryorcashman'
    allowed_domains = ['pryorcashman.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        self.listing_template = 'https://www.pryorcashman.com/people?search[post_type]=person&from={}'
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False) 
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.listing_template.format(0))
            page.wait_for_selector('div[role=navigation] span')
            total_pages = max([int(number) for number in findall('\d+',page.query_selector_all('div[role=navigation] span')[0].inner_text())])
            self.start_urls += ['https://www.pryorcashman.com'+handle.get_attribute('href') for handle in page.query_selector_all('//a[contains(text(),"Email")]/preceding-sibling::a')]
            self.logger.info('extracted urls : {}'.format(len(self.start_urls)))
            for page_id in range(2,total_pages +1):
                page.goto(self.listing_template.format((page_id-1)*30))
                page.wait_for_selector('div[role=navigation] span')
                self.start_urls += ['https://www.pryorcashman.com'+handle.get_attribute('href') for handle in page.query_selector_all('//a[contains(text(),"Email")]/preceding-sibling::a')]
                self.logger.info('extracted urls : {}'.format(len(self.start_urls)))


    def parse(self,response):
        url = response.url
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            page.wait_for_selector('//h1')
            response = Selector(text=page.content())

        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
        fullname_list = response.xpath('string(//h1)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/ancestor::div[2]/following-sibling::div//text()')
        loader.add_xpath('email','//a[contains(@href,"@pryorcashman.com")]/text()')
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
        loader.add_xpath('image','//img/@src')
        loader.add_xpath('bio','string(//div[@role="main"])')
        loader.add_value('firm_bio','https://www.pryorcashman.com/about-us')
        loader.add_xpath('office','//a[contains(@href,"office-locations")]/text()')
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


                