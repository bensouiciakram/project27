import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import json


class StoelSpider(scrapy.Spider):
    name = 'stoel'
    allowed_domains = ['stoel.com']
    start_urls = ['http://stoel.com/']


    def start_requests(self):
        yield Request(
            'https://www.stoel.com/siteapi/attorney/search',
            method='POST',
            headers= {
                'Content-Type': 'application/json;charset=UTF-8'
            },
            body = json.dumps({'CurrentPage': 1, 'PageCount': 1000}),
            callback= self.parse_individuals
        )



    def parse_individuals(self,response):
        people_urls = [response.urljoin(item['URL']) for item in response.json()['Items']]
        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.basic-info-section h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.position::text')
        loader.add_css('email','a.email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul[1]/li')]
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
        loader.add_value('image',response.urljoin(response.css('div.attorney-bio-info img::attr(src)').get()))
        loader.add_xpath('bio','string(//section[@id="overview"])')
        loader.add_value('firm_bio','https://www.stoel.com/about-stoel-rives')
        loader.add_css('office','span.location::text')
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