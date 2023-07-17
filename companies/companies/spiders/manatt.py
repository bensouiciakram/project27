import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from math import ceil


class ManattSpider(scrapy.Spider):
    name = 'manatt'
    allowed_domains = ['manatt.com']
    start_urls = ['http://manatt.com/']

    def __init__(self):
        self.listing_template = 'https://www.manatt.com/search/people?searchmode=anyword&page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1)
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback= self.parse_individuals,
                dont_filter= True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('h3.name a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h4.blue-lt span.eng::text')
        loader.add_xpath('email','//a[contains(@href,"mailto")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//a[contains(text(),"Education")]/ancestor::div[1]/following-sibling::div//p')]
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
        loader.add_value('image',response.urljoin(response.css('figure img::attr(src)').get()))
        loader.add_xpath('bio','string(//h2[contains(text(),"Profile")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.manatt.com/about')
        loader.add_xpath('office','//li[contains(@class,"location")]/a/text()')
        yield loader.load_item()


    def get_total_pages(self,response):
        return ceil(max([int(number) for number in response.xpath('//script[contains(text(),"showing results")]').re('\d+')])/10)


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