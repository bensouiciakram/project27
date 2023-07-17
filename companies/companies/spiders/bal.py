import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'bal'
    allowed_domains = ['bal.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']\
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.bal.com/people/')
            page.click('div h4 i')
            page.wait_for_timeout(5000)
            self.start_urls = {handle.get_attribute('href') for handle in page.query_selector_all('div.person-data h4 a')}
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
        loader.add_css('title','h3.primary::text')
        loader.add_xpath('email','//a[contains(@href,"@bal.com")]/text()')
        educations_list = [edu.get() for edu in response.xpath('//span[contains(text(),"Education & Admissions")]/ancestor::h3/following-sibling::p/text()')]
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
        loader.add_css('image','img.attachment-full::attr(src)')
        loader.add_xpath('bio','(//section)[last()]/p/text()')
        loader.add_value('firm_bio','https://www.bal.com/about/')
        loader.add_xpath('office','(//section)[2]//tr[last()]/td[1]/text()[1]')
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


                