import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.selector import Selector 


class MaynardcooperSpider(scrapy.Spider):
    name = 'maynardcooper'
    allowed_domains = ['maynardcooper.com']
    start_urls = ['http://maynardcooper.com/']

    def __init__(self):
        self.listing_template = 'https://www.maynardcooper.com/index.php?p=actions/maynardcooper&offset={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            callback=self.parse_individuals,
            meta={
                'page':0
            }
        )

    def parse_individuals(self, response):
        selector = Selector(text=response.json()['html'])
        people_urls = selector.css('a::attr(href)').getall()
        if not people_urls :
            return 
        for url in people_urls :
            yield Request(
                url,
                callback = self.parse_individual
            )
        page = response.meta['page'] + 1
        yield Request(
            self.listing_template.format(page*12),
            callback = self.parse_individuals,
            meta={
                'page':page
            }
        )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::p/text()')
        loader.add_xpath('email','(//a[contains(@href,"mailto")])[1]/text()')
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//h5[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_xpath('image','//h1/ancestor::div[1]/following-sibling::div//img/@src')
        loader.add_xpath('bio','string(//h3[contains(text(),"Profile")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.maynardcooper.com/firm')
        loader.add_xpath('office','string(//h1/preceding-sibling::span)')
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