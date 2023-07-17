import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class GrayRobinsonSpider(scrapy.Spider):
    name = 'gray_robinson'
    allowed_domains = ['gray-robinson.com']
    start_urls = ['http://gray-robinson.com/']

    def __init__(self):
        self.listing_template = 'https://www.gray-robinson.com/attorneys/by-letter/{}'


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch),
                callback= self.parse_individuals
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.xpath('//div[@class="profile-card"]//a[1]/@href').getall()]
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
        loader.add_xpath('title','//p[contains(@class,"profile-title")][1]/text()')
        loader.add_css('email','p.profile-email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//a[contains(text(),"Education")]/following-sibling::div/ul/li')]
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
        loader.add_value('image',response.urljoin(response.css('img.profile-headshot::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="bio cell"]/p)')
        loader.add_value('firm_bio','https://www.gray-robinson.com/')
        loader.add_value('office',response.xpath('//span[@id="Address1"]/span[last()]/text()').get().split(',')[0])
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