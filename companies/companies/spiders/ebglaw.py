import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright._impl._api_types import TimeoutError


class EbglawSpider(scrapy.Spider):
    name = 'ebglaw'
    allowed_domains = ['ebglaw.com']
    start_urls = ['http://ebglaw.com/']

    def __init__(self):
        self.listing_template = 'https://www.ebglaw.com/people/?page={}'
        self.start_urls = set()
        with sync_playwright() as p : 
            self.run(p)


            
    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h1)').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.position::text')
        loader.add_xpath('email','//span[contains(text(),"@ebglaw.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('li.education-entry')]
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

        loader.add_css('image','figure img::attr(src)')
        loader.add_xpath('bio','string(//div[@itemprop="description"])')
        loader.add_value('firm_bio','https://www.curtis.com/our-firm/about')
        loader.add_css('office','p.bio-hero__block-info-cont-sub a::text')
        yield loader.load_item()



    # def get_data(self,response):
    #     # there is a mistake on the test line 
    #     if '?sitecoreItemUri' in response.url :
    #         if len(response.json()['results']) == 2 :
    #             people_urls = {individual['url'] for individual in response.json()['results'][0]['hits'] if individual['attorneyTitle']}
    #             self.start_urls = self.start_urls.union(people_urls)
    #             self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
    #             return response.json()    


    def run(self,p):
        browser = p.chromium.launch()#headless=False)
        context = browser.new_context()
        page = context.new_page()
        #page.on('response',self.get_data)
        page_id = 1
        page.goto(self.listing_template.format(1))
        page.wait_for_selector('h2 a',timeout=120000)
        people_urls = {individual.get_attribute('href') for individual in page.query_selector_all('h2 a')}
        self.start_urls = self.start_urls.union(people_urls)
        self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
        while True :
            page_id += 1
            page.goto(self.listing_template.format(page_id))
            try :
                page.wait_for_selector('h2 a')
            except TimeoutError : 
                pass
            people_urls = {individual.get_attribute('href') for individual in page.query_selector_all('h2 a')}
            self.start_urls = self.start_urls.union(people_urls)
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            if not people_urls :
                break

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