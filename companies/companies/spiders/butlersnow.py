import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import json

class ButlersnowSpider(scrapy.Spider):
    name = 'butlersnow'
    allowed_domains = ['butlersnow.com']
    start_urls = ['http://butlersnow.com/']

    def __init__(self):
        self.listing_template = 'https://www.butlersnow.com/professionals/attorney-professional-search/?search=true'
        self.individual_template = 'https://www.butlersnow.com/{}/{}/'
        self.start_urls = set()
        with sync_playwright() as p : 
            self.run(p)


            
    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1.page-title::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        # no title found
        #loader.add_xpath('title','')
        loader.add_value('email',response.css('a.attorney-email::attr(href)').get().replace('mailto:',''))
        

        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('(//a[contains(text(),"Education & Honors")])[2]/ancestor::h3/following-sibling::div/ul/li')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try: 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError : 
            pass

        loader.add_css('image','img.attorney-photo::attr(src)')
        loader.add_css('bio','blockquote::text')
        loader.add_value('firm_bio','https://www.butlersnow.com/firm/about-us/')
        loader.add_xpath('office','string(//ul[@class="attorney-offices"]/li )')
        yield loader.load_item()


    def get_data(self,response):
        try:
            if 'admin-ajax.php' in response.url :
                people_urls = {self.individual_template.format(item['post_type'],item['post_name']) for item in response.json()}
                self.start_urls = self.start_urls.union(people_urls)
                self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
                return response.json()    
        except json.decoder.JSONDecodeError : 
            pass


    def run(self,p):
        browser = p.chromium.launch()#headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        page.goto(self.listing_template,timeout=60000)


    def get_total_page(self,page):
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