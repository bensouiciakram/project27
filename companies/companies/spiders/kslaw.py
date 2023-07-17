import scrapy
import json
from math import ceil 
from scrapy import Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall

class KslawSpider(scrapy.Spider):
    name = 'kslaw'
    allowed_domains = ['kslaw.com']
    start_urls = ['https://www.kslaw.com/people?locale=en&page=1&per_page=96&q=']


    def __init__(self):
        self.listing_template = 'https://www.kslaw.com/people?locale=en&page={}&per_page=96&q='

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1) : 
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter = True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('h2 a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader  = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        loader.add_css('first_name','span.first_name::text')
        loader.add_css('last_name','span.last_name::text')
        loader.add_xpath('title','//h1/following-sibling::p/text()')
        loader.add_xpath('email','//a[contains(text(),"@kslaw.com")]/text()')
        educations_list = set([edu.xpath('string(.)').get() for edu in response.xpath('//div[@class="cred education"]/p')])
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
        loader.add_value('firm_bio','https://www.kslaw.com/pages/about')
        loader.add_xpath('bio','string(//div[@class="bio_hed"])')
        loader.add_xpath('office','//div[@class="contacts"]/p[1]/a[1]/text()')
        yield loader.load_item()

    def get_total_pages(self,response):
        return ceil(json.loads(response.css('pagination-links').attrib[':value'])['totalEntries']/96)


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