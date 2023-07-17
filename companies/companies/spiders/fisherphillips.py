import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem



class FisherphillipsSpider(scrapy.Spider):
    name = 'fisherphillips'
    allowed_domains = ['fisherphillips.com']
    start_urls = ['http://fisherphillips.com/']

    def __init__(self):
        self.listing_template = 'https://www.fisherphillips.com/people/?f={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            meta= {
                'page':0
            }
            )


    def parse(self, response):
        if 'No results found.' in response.text : 
            return 
        people_urls = response.css('dt a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )
        page = response.meta['page']
        page += 1
        yield Request(
            self.listing_template.format(page*20),
            meta={
                'page':page
            }
        )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','string(//h1/following-sibling::p)')
        loader.add_value('email',response.xpath('//a[contains(text(),"Email")]/@href').get().replace('mailto:',''))
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
        loader.add_css('image','picture img::attr(src)')
        loader.add_xpath('bio','string(//h3[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','')
        loader.add_xpath('office','(//a[contains(@class,"u-underline-on-hover")])[1]/text()')
        yield loader.load_item()


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