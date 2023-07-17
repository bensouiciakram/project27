import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
from playwright._impl._api_types import TimeoutError
from scrapy import Selector 
import re


class SkaddenSpider(scrapy.Spider):
    name = 'ralaw'
    allowed_domains = ['ralaw.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['E.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')
            context = browser.new_context()
            page = context.new_page()
            #page.on('response',lambda response:print(response.url))
            try:
                page.goto('https://www.ralaw.com/people?viewall=true',timeout=15000)
            except TimeoutError:
                pass
            response = Selector(text=page.content())
        self.start_urls = ['https://www.ralaw.com' + url for url in response.xpath('//td[@data-sort-value]/a/@href').getall()]
        self.logger.info('extracted urls : {}'.format(len(self.start_urls)))


    def parse(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
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
        loader.add_xpath('title','//h1/following-sibling::h6/text()')
        loader.add_xpath('email','//a[contains(text(),"@ralaw.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[@id="education-tab"]//ol/li')]
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
        loader.add_css('image','div.attorney_bio_pic::attr(style)')
        loader.add_xpath('bio','string(//div[@id="overview-tab"]/div/div[2])')
        loader.add_value('firm_bio','https://www.ralaw.com/about')
        loader.add_xpath('office','(//a[contains(@href,"/offices")])[last()]/text()')
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
