import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class WcSpider(scrapy.Spider):
    name = 'wc'
    allowed_domains = ['wc.com']
    start_urls = ['http://wc.com/']

    def __init__(self):
        self.listing_template = 'https://www.wc.com/Attorneys/Search?alpha={}'


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                callback=self.parse_individuals
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('a.bio_name_wrapper::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.atty_full_name h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.atty_titles::text')
        loader.add_css('email','div.bio_email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h1[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_value('image',response.urljoin(response.css('img.bio_img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="bio_short_overview"])')
        loader.add_value('firm_bio','https://www.wc.com/Firm')
        # office not found
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