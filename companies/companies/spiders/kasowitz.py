import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class KasowitzSpider(scrapy.Spider):
    name = 'kasowitz'
    allowed_domains = ['kasowitz.com']
    start_urls = ['http://kasowitz.com/']


    def __init__(self):
        self.listing_template = 'https://www.kasowitz.com/people/search-results?page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
        )


    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback = self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('a.spotlight_media_link::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual,
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//ul[@class="vcard"]/li[1]/text()').get().strip().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.role::text')
        loader.add_css('email','a.email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('div#panel-Education li')]
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
        loader.add_value('image',response.urljoin(response.css('div.hero_media img::attr(src)').get()))
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.xpath('//div[@class="tabs"]/preceding-sibling::p')]))
        loader.add_value('firm_bio','https://www.kasowitz.com/at-a-glance')
        loader.add_css('office','span.region::text')
        yield loader.load_item()


    def get_total_pages(self,response):
        return min([int(number) for number in response.xpath('//div[@class="pagination_summary"]/div/text()').re('\d+')])


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