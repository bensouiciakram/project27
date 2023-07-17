import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class CarltonfieldsSpider(scrapy.Spider):
    name = 'carltonfields'
    allowed_domains = ['carltonfields.com']
    start_urls = ['http://carltonfields.com/']

    def __init__(self):
        self.listing_template = 'https://www.carltonfields.com/team#page={}'
        self.total_pages = 0
        self.start_urls = set()
        with sync_playwright() as p : 
            self.run(p)


            
    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().strip().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::h5/text()')
        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            loader.add_value('email',page.query_selector('//a[contains(@href,"mailto")]').get_attribute('href').replace('mailto:',''))

        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h5[contains(text(),"Education")]/following-sibling::div//li')]
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

        loader.add_value('image',response.urljoin(response.css('div.wrap--bio--img img::attr(src)').get()))
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.xpath('//h2[contains(text(),"Overview")]/following-sibling::p')]))
        loader.add_value('firm_bio','https://www.carltonfields.com/about-us')
        loader.add_xpath('office','//a[contains(@href,"offices")]/text()')
        yield loader.load_item()


    def get_data(self,response):
        if 'api/attorneysearch/search' in response.url :
            people_urls = {'https://www.carltonfields.com' + individual['URL'] for individual in response.json()['Items']}
            self.total_pages = response.json()['TotalItems']
            self.start_urls = self.start_urls.union(people_urls)
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            return response.json()    


    def run(self,p):
        browser = p.chromium.launch()#headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        page.goto(self.listing_template.format(1),timeout=60000)
        page.wait_for_timeout(3000)
        for index in range(2,self.total_pages + 1):
            page.click('a.next')
            page.wait_for_timeout(3000)

        
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