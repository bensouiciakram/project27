import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class BskSpider(scrapy.Spider):
    name = 'bsk'
    allowed_domains = ['bsk.com']
    start_urls = ['https://www.bsk.com/people?nopagination=true']


    def parse(self, response):
        people_urls = response.css('h3 a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::h2/text()')
        loader.add_css('email','span.disclaimer-btn::text')
        educations_list = set([edu.xpath('string(.)').get().strip() for edu in response.xpath('//a[contains(text(),"Education")]/following-sibling::div/ul/li')])
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
        loader.add_css('image','picture img::attr(style)',re='background-image:url\(  (\S+)')
        loader.add_xpath('bio','string(//div[@aria-label="Profile expanded"])')
        loader.add_value('firm_bio','https://www.bsk.com/our-firm/about-bond')
        loader.add_xpath('office','//span[@class="disclaimer-btn"]/following-sibling::a[1]/text()')
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