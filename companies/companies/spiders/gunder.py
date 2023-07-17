import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import json 


class GunderSpider(scrapy.Spider):
    name = 'gunder'
    allowed_domains = ['gunder.com']
    start_urls = ['https://www.gunder.com/']

    def __init__(self):
        self.listing_template = 'https://www.gunder.com/people/page/{}/?search%5Bkeyword%5D='


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
            meta={
                'page':1
            }
        )

    def parse(self, response):
        people_urls = response.xpath('//a[contains(@id,"post")]/@href').getall()
        if not people_urls:
            return 
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )
        page = response.meta['page'] + 1
        yield Request(
            self.listing_template.format(page),
            meta={
                'page':page
            }
        )

    def parse_individuals(self,response):
        pass


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div#attorney-name::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.person-title::text')
        loader.add_value('email',json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get())['email'])
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('ul.education-list>li')]
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
        loader.add_xpath('image','(//section[@id="attorney-info"]//img)[1]/@src')
        loader.add_xpath('bio','string(//div[@class="description"])')
        loader.add_value('firm_bio','https://www.gunder.com')
        loader.add_css('office','div.office-location span::text')
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