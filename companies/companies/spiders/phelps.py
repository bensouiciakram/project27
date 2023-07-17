import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class PhelpsSpider(scrapy.Spider):
    name = 'phelps'
    allowed_domains = ['phelps.com']
    start_urls = ['http://phelps.com/']

    def __init__(self):
        self.listing_template = 'https://www.phelps.com/professionals/index.html?f={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            callback= self.parse_individuals ,
            meta = {
                'page':0
            }
        )


    def parse_individuals(self,response):
        people_urls = response.css('dt a::attr(href)').getall()
        page = response.meta['page']
        if not people_urls :
            return 
        else :
            page += 1 
            yield Request(
                self.listing_template.format(page*20),
                callback=self.parse_individuals,
                meta= {
                    'page':page
                }
            )

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
        loader.add_xpath('title','//h1/following-sibling::p/text()')
        loader.add_value('email',response.xpath('//a[contains(@href,"mailto")]/@href').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('(//span[contains(text(),"Education")]/ancestor::h2/following-sibling::div//ul)[1]/li')]
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
        loader.add_xpath('bio','string(//div[@id="overview"])')
        loader.add_value('firm_bio','https://www.phelps.com/our-firm/about-our-firm/index.html')
        loader.add_xpath('office','//div[contains(@class,"contactInfoContainer")]/div[1]/a')
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