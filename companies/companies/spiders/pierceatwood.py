import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
import traceback 
import re 


class SkaddenSpider(scrapy.Spider):
    name = 'pierceatwood'
    allowed_domains = ['pierceatwood.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.pierceatwood.com/people')
            while True :
                page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight);')
                page.wait_for_timeout(5000)
                urls = ['https://www.pierceatwood.com' + handle.get_attribute('href') for handle in page.query_selector_all('article div.row>a')]
                if len(self.start_urls) >= len(urls):
                    break
                self.start_urls = urls 
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
        loader.add_xpath('title','//h6/text()')
        loader.add_css('email','div.field--type-email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::div//div[@class="field__item"]')]
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
        loader.add_css('image','img.image-style-headshot::attr(src)')
        loader.add_xpath('bio','string(//div[contains(@class,"field--name-field-abbreviated-bio")])')
        loader.add_value('firm_bio','https://www.pierceatwood.com/firm')
        loader.add_css('office','h6 a::text')
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


                