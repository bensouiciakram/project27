import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from math import ceil


class IcemillerSpider(scrapy.Spider):
    name = 'icemiller'
    allowed_domains = ['icemiller.com']
    start_urls = ['http://icemiller.com/']

    def __init__(self):
        self.listing_template = 'https://www.icemiller.com/people/attorneys/search/?page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('a.name::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::h3/text()')
        loader.add_xpath('email','//p[@class="attorney-contact"]/a[1]/text()')
        educations_list = []
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
        loader.add_value('image',response.urljoin(response.xpath('//h3/following-sibling::div/img/@src').get()))
        loader.add_xpath('bio','string(//div[@id="Overview"])')
        loader.add_value('firm_bio','https://www.icemiller.com/firm/overview/')
        loader.add_css('office','h3 strong::text')
        yield loader.load_item()


    def get_total_pages(self,response):
        return ceil(max([int(number) for number in response.xpath('//div[@class="PagerResults"]').re('\d+')])/40)


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