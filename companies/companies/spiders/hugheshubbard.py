import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.selector import Selector 

class HugheshubbardSpider(scrapy.Spider):
    name = 'hugheshubbard'
    allowed_domains = ['hugheshubbard.com']
    start_urls = ['https://www.hugheshubbard.com/xhr/search_people.json?starts-with%5B%5D=']


    def parse(self, response):
        people_urls = [Selector(text=item['dom']).xpath('//a/@href').get() for item in response.json()['data']]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.headers__sub_title h2::text')
        loader.add_xpath('email','//a[contains(@href,"mailto")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//strong[contains(text(),"Education")]/ancestor::div[1]/following-sibling::div/ul/li')]
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
        loader.add_css('image','div.image img::attr(src)')
        loader.add_xpath('bio','string(//div[@data-hash="Biography"])')
        loader.add_value('firm_bio','https://www.hugheshubbard.com/culture/about-us')
        loader.add_xpath('office','//div[@class="headers__contact-row"][1]/p/text()')
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