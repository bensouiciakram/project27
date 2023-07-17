import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class AdamsandreeseSpider(scrapy.Spider):
    name = 'adamsandreese'
    allowed_domains = ['adamsandreese.com']
    start_urls = ['http://adamsandreese.com/']

    def __init__(self):
        self.listing_template = 'https://www.adamsandreese.com/people?letter={}&pageNumber=50'


    def start_requests(self):
        for ch in 'abcdefgijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                callback= self.parse_individuals
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.xpath('//div[contains(@class,"gridlist__section")][1]/a/@href').getall()]
        emails = response.xpath('//a[contains(text(),"@arlaw.com")]/text()').getall()
        for url,email in zip(people_urls,emails): 
            yield Request(
                url,
                callback= self.parse_individual,
                meta={
                    'email':email
                }
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2.profilecard__subtitle::text')
        loader.add_value('email',response.meta['email'])
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/ancestor::div[1]/following-sibling::div/ul/li')]
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
        loader.add_css('image','div.hero__image::attr(style)',re='\((\S+)\)')
        loader.add_xpath('bio','string(//main[contains(@class,"page__content")])')
        loader.add_value('firm_bio','https://www.adamsandreese.com/about')
        loader.add_css('office','a.profilecard__location span::text')
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