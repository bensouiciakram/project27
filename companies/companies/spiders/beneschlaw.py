import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class BeneschlawSpider(scrapy.Spider):
    name = 'beneschlaw'
    allowed_domains = ['beneschlaw.com']
    start_urls = ['http://beneschlaw.com/']

    def parse(self, response):
        pass

    def __init__(self):
        self.listing_template = 'https://www.beneschlaw.com/people/index.html?f={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0)
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(20*page),
                callback = self.parse_individuals,
                dont_filter = True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('dt a::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1 div::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//div[contains(@class,"subtitle")]/text()')
        loader.add_value('email',findall('"email": "(\S+@\S+)"',response.text)[0])
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//div[contains(text(),"Education")]/ancestor::button/following-sibling::div/ul/li')]
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
        loader.add_css('image','picture img::attr(src)')
        loader.add_xpath('bio','string(//ul[@role="tablist"]/following-sibling::div[1])')
        loader.add_value('firm_bio','https://www.beneschlaw.com/about.html')
        loader.add_xpath('office','string(//div[contains(@class,"office-contact")]/preceding-sibling::div)')
        yield loader.load_item()


    def get_total_pages(self,response):
        return max([int(number) for number in response.xpath('//button[contains(@class,"pagination")]/text()').getall()])


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