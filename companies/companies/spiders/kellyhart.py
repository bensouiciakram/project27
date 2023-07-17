import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
from playwright._impl._api_types import TimeoutError
import traceback 
from scrapy import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'kellyhart'
    allowed_domains = ['kellyhart.com']
    start_urls = []


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        self.listing_template = 'https://www.kellyhart.com/attorneys?search[letter]={}'
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            for ch in 'abcdefghijklmnopqrstuvwxyz':
                page.goto(self.listing_template.format(ch.upper()))
                try :
                    page.wait_for_selector('//div[contains(@class,"result_data")]/a[1]',timeout=5000)
                except TimeoutError :
                    continue
                self.start_urls += ['https://www.kellyhart.com'+ handle.get_attribute('href') for handle in page.query_selector_all('//div[contains(@class,"result_data")]/a[1]')]
                self.logger.info('the extracted urls : {}'.format(len(self.start_urls)))


    def parse(self,response):
        url = response.url
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            page.wait_for_selector('//h2')
            response = Selector(text=page.content())
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
        fullname_list = response.xpath('//h2/text()').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.ai_atitle::text')
        loader.add_css('email','div.email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h6[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_css('image','div#banner-img::attr(style)')
        loader.add_xpath('bio','string(//h6[contains(text(),"Biography")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.kellyhart.com/about-us')
        loader.add_value('office','')
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


                