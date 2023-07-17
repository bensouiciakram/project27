import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall

class KlgatesSpider(scrapy.Spider):
    name = 'klgates'
    allowed_domains = ['klgates.com']
    start_urls = ['http://klgates.com/']

    def __init__(self):
        self.listing_template = 'https://www.klgates.com/Bio/Search?LangCode=en-US&alpha={}&pageSize=9999'


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                callback = self.parse_individuals
            )


    def parse_individuals(self, response):
        people_urls = [response.urljoin(url) for url in response.css('a.s-bio-card__heading::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.job-title::text')
        loader.add_value('email',response.xpath('//span[contains(text(),"Email")]/following-sibling::span/text()').get().split('@',1)[-1])
        educations_list = [sel.xpath('string(.)').get().strip() for sel in response.xpath('//h3[contains(text(),"Education")]/ancestor::button/following-sibling::div//li')]
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
        loader.add_css('image','div.head-shot-wrap img::attr(src)')
        loader.add_xpath('bio','string(//h3[contains(text(),"Overview")]/ancestor::button/following-sibling::div)')
        loader.add_value('firm_bio','https://www.klgates.com/firm-overview')
        loader.add_css('office','a.location-name::text')
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
    
    