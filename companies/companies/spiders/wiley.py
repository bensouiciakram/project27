import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class WileySpider(scrapy.Spider):
    name = 'wiley'
    allowed_domains = ['wiley.law']
    start_urls = ['http://wiley.com/']

    def __init__(self):
        self.listing_template = 'https://www.wiley.law/people?page={}&do_item_search=1'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1)
        )

    def parse(self, response):
        total_pages = int(response.css('a.last::text').get())
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('div.title a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        loader.add_css('first_name','span[itemprop="givenName"]::text')
        loader.add_css('last_name','span[itemprop="familyName"]::text')
        loader.add_value('firm',self.name)
        loader.add_css('title','div#bioTitle::text')
        loader.add_css('email','li#bioEmail a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::p')]
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
        loader.add_value('image',response.urljoin(response.css('div#bioPhoto img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@id="bio_content"])')
        loader.add_value('firm_bio','https://www.wiley.law/about')
        # no office found 
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