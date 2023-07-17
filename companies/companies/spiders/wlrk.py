import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem

class WlrkSpider(scrapy.Spider):
    name = 'wlrk'
    allowed_domains = ['wlrk.com']
    start_urls = ['http://wlrk.com/']

    def __init__(self):
        self.listing_template = 'https://www.wlrk.com/attorneys/?asf_n=&asf_pa=&asf_ls=&asf_p=&asf_ugs=&asf_l={}'


    def start_requests(self):
        for ch in 'abcdefgijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                callback= self.parse_individuals,
            )


    def parse_individuals(self,response):
        people_urls = response.css('ul.attorneys-search--results-items li a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','li.attorney--meta-positions::text')
        loader.add_xpath('email','//a[contains(@href,"mailto:")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','div.attorney--image img::attr(src)')
        loader.add_xpath('bio','string(//div[@class="attorney--biography"])')
        loader.add_value('firm_bio','https://www.wlrk.com/firm/')
        # no location found 
        #loader.add_('office',)
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