import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall
from playwright.sync_api import sync_playwright 

class WhitecaseSpider(scrapy.Spider):
    name = 'whitecase'
    allowed_domains = ['whitecase.com']
    start_urls = ['https://www.whitecase.com/people-export/lawyers.json']

    def parse(self, response):
        data = response.json()
        people_urls = [ individual['path'] for individual in data ]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )

    
    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1 span::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm','whitecase')
        title_and_office = response.css('div.heading__bio-info::text').get().strip().split(',')
        loader.add_value('title',title_and_office[0])
        loader.add_value('office',title_and_office[1])
        with sync_playwright() as p : 
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            loader.add_value('email',page.query_selector('div.field--name-field-email a').inner_text())
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//div[contains(text(),"Education")]/following-sibling::div/div')]
        try:
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
        loader.add_value('firm_bio','https://www.whitecase.com/#home-about-us')
        loader.add_value('image',response.urljoin(response.css('picture img::attr(src)').get()))
        loader.add_xpath('bio','string(//h3[contains(text(),"Overview")]/following-sibling::div[1])')
        yield loader.load_item()





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