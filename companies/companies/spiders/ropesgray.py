import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall

class RopesgraySpider(scrapy.Spider):
    name = 'ropesgray'
    allowed_domains = ['ropesgray.com']
    start_urls = ['http://ropesgray.com/']


    def __init__(self):
        self.listing_template = 'https://www.ropesgray.com/en/biographies?l={}&li={}'

    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch,0),
                meta= {
                    'page':1,
                    'ch':ch
                }
            )


    def parse(self,response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(response.meta['ch'],24*page),
                callback = self.parse_individuals
            )

    def parse_individuals(self,response):
        people_urls =  [response.urljoin(url) for url in response.css('h4 a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )

    def parse_individual(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2.title::text')
        loader.add_xpath('email','//a[contains(text(),"@ropesgray.com")]/text()')
        educations_list = set([edu.xpath('string(.)').get() for edu in response.css('div#module-education li')])
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
        loader.add_value('bio',' '.join(response.xpath('//hgroup[@class="hidden-phone"]/following-sibling::p/text()').getall()))
        loader.add_xpath('office','//abbr/following-sibling::a/text()')
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.css('span.total-pages::text').get())

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