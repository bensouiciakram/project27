import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem



class ReinhartlawSpider(scrapy.Spider):
    name = 'reinhartlaw'
    allowed_domains = ['reinhartlaw.com']
    start_urls = ['http://reinhartlaw.com/']

    def __init__(self):
        self.listing_template = 'https://www.reinhartlaw.com/people/?lastname={}'
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                callback= self.parse_individuals
            )


    def parse_individuals(self,response):
        people_urls = response.css('h3 a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','li.title::text')
        loader.add_css('email','li.email a::text')
        educations_list = [edu.get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::p[1]/text()')]
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
        loader.add_css('image','div.attorney_bio_photo img::attr(src)')
        loader.add_xpath('bio','string(//div[@class="bio"])')
        loader.add_value('firm_bio','https://www.reinhartlaw.com/about-us/')
        loader.add_css('office','li.locations a::text')
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