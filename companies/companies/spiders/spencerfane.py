import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SpencerfaneSpider(scrapy.Spider):
    name = 'spencerfane'
    allowed_domains = ['spencerfane.com']
    start_urls = ['https://www.spencerfane.com/attorneys/?first_name=&last_name=&practice_id=&industry_id=&position_id=&bar_id=&court_id=&office_id=&education_id=&keyword=&submit=search']

    def parse(self, response):
        people_urls = response.css('h2 a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.content h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','p.attorney-position::text')
        loader.add_xpath('email','//a[contains(@href,"mailto")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul[1]/li')]
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
        loader.add_css('image','div.attorney-photos img::attr(src)')
        loader.add_xpath('bio','string(//div[contains(@class,"tab-content")])')
        loader.add_value('firm_bio','https://www.spencerfane.com/our-firm/')
        loader.add_xpath('office','//div[@class="attorney-contact-info"]//div[2]//li/a/text()')
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