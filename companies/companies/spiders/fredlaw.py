import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class FredlawSpider(scrapy.Spider):
    name = 'fredlaw'
    allowed_domains = ['fredlaw.com']
    start_urls = ['http://fredlaw.com/']


    def __init__(self):
        self.listing_template = 'https://www.fredlaw.com/our_people/?page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1)
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback= self.parse_individuals ,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = response.xpath('//div[@class="person-info-item person-name"]/a/@href').getall()
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            ) 


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        try :
            fullname_list = response.xpath('//h1/text()').get().split()
        except AttributeError :
            fullname_list = response.xpath('string(//h1)').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h3 span::text')
        loader.add_xpath('email','//p[contains(text(),"Email")]/a/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"EDUCATION")]/following-sibling::ul[1]/li')]
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
        loader.add_css('image','span.image_component img::attr(src)')
        loader.add_xpath('bio','string(//span[contains(text(),"Overview")]/ancestor::a/following-sibling::div)')
        loader.add_value('firm_bio','https://www.fredlaw.com/our_firm/')
        # office not found 
        #loader.add_('office',)
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.xpath('//h4[@class="pagination-count"]/strong[last()]/text()').get())


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
