import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
import re 
from playwright._impl._api_types import TimeoutError

class SkaddenSpider(scrapy.Spider):
    name = 'bowmanandbrooke'
    allowed_domains = ['bowmanandbrooke.com']
    start_urls = ['https://www.bowmanandbrooke.com/attorneys/attorneys-listing']

    def __init__(self):
        self.not_names = ['Z.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome',headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.start_urls[0])
            while True :
                try :
                    page.click('div.more a')
                except TimeoutError:
                    pass
                with page.expect_response(re.compile(r"^https://www.bowmanandbrooke.com/attorneys/attorneys-listing"),timeout=60000) as response_info:
                    response = response_info.value
                    total_urls  = response.json()['TotalItems']
                self.start_urls = ['https://www.bowmanandbrooke.com' + handle.get_attribute('href') for handle in page.query_selector_all('div.name a')]
                self.logger.info('total urls extracted : {}'.format(len(self.start_urls)))
                if len(self.start_urls) == total_urls :
                    break






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
        loader.add_xpath('title','//div[@class="name"]/following-sibling::div[@class="title"]/text()')
        loader.add_css('email','div.email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('div.education li')]
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
        loader.add_value('image',response.urljoin(response.css('div.image img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="biodetail"])')
        loader.add_value('firm_bio','https://www.bowmanandbrooke.com/our-firm/overview')
        loader.add_css('office','ul.location li::text')
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


                