import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import json 


class WshblawSpider(scrapy.Spider):
    name = 'wshblaw'
    allowed_domains = ['wshblaw.com']
    start_urls = ['https://www.wshblaw.com/attorneys/?locations%5B%5D=&practiceareas%5B%5D=&title_category=&lawschools%5B%5D=&admitted%5B%5D=&']


    def parse(self, response):
        people_urls = response.xpath('//div[@class="col name italhead"]/a/@href').getall()
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h3.name::text').get().strip().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.patternblock h3::text')
        loader.add_css('email','span.email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::div/p')]
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
        loader.add_value('image',self.get_image(response))
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.xpath('//h2[contains(text(),"Bio")]/following-sibling::p')]))
        loader.add_value('firm_bio','https://www.wshblaw.com/our-firm/')
        loader.add_xpath('office','//div[@class="locations"]//text()[3]')
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



    def get_image(self,response):
        data = json.loads(response.css('script.yoast-schema-graph::text').get())['@graph']
        for item in data : 
            if item['@type'] == 'ImageObject' :
                return item['url']