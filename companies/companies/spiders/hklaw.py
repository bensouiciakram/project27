import scrapy
from math import ceil
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall

class HklawSpider(scrapy.Spider):
    name = 'hklaw'
    allowed_domains = ['hklaw.com']
    start_urls = ['http://hklaw.com/']

    
    def __init__(self):
        self.listing_template = 'https://www.hklaw.com/api/ProfessionalsApi/Lawyers?&page={}'

    
    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            method='POST'
        )
        


    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages) :
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                method='POST',
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(individual['url']) for individual in response.json()['results']]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h5::text')
        loader.add_css('email','a.bio-card__link--email span::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_value('firm_bio','https://www.hklaw.com/en/firm/firm-culture')
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview ")]/following-sibling::div)')
        loader.add_xpath('office','//a[@class="bio-card__office-link"][1]/text()')
        yield loader.load_item()

    def get_total_pages(self,response):
        return ceil(response.json()['total']/20)


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