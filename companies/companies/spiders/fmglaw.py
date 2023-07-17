import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'fmglaw'
    allowed_domains = ['fmglaw.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['T.','H.','Y.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        self.listing_template = 'https://www.fmglaw.com/our-people/?letter={}&fpage=1&keyword='
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            for ch in 'abcdefgijklmnopqrstuvwxyz':
                page.goto(self.listing_template.format(ch.upper()))
                try:
                    page.wait_for_selector('div.bio-card>a',timeout=5000)
                except :
                    continue
                self.start_urls += [handle.get_attribute('href') for handle in page.query_selector_all('div.bio-card>a')]
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
        loader.add_css('title','p.position::text')
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            loader.add_value('email',page.query_selector('//a[contains(@href,"@fmglaw.com")]').inner_text())
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','img.img::attr(src)')
        loader.add_xpath('bio','string(//a[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.fmglaw.com/who-we-are/')
        loader.add_xpath('office','//p[@class="position"]/following-sibling::p/a[1]/text()')
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


                