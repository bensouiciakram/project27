import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'skadden'
    allowed_domains = ['skadden.com']
    start_urls = ['http://skadden.com/']


    def __init__(self):
        self.listing_template = 'https://www.skadden.com/api/sitecore/professionals/search?skip={}&letter={}'


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(0,ch.upper()),
                meta = {
                    'ch':ch
                }
            )
        

    def parse(self, response):
        total_pages = (response.json()['ResultCount'] - 5)//10 +1 
        yield Request(
            response.url,
            callback=self.parse_individuals,
            dont_filter = True
        )
        ch = response.meta['ch']
        for page in range(total_pages) : 
            yield Request(
                self.listing_template.format(5 + 10*page,ch),
                callback = self.parse_individuals
            )


    def parse_individuals(self,response):
        data = response.json()
        people_urls = [response.urljoin(individual['Url']) for individual in data['SearchResults']]
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
        loader.add_css('title','div.profile-header-position::text')
        loader.add_css('email','a.profile-header-email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_value('image',response.urljoin(response.css('img.profile-header-snapshot::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="impactful-lead "])')
        loader.add_value('firm_bio','https://www.skadden.com/About/Overview')
        loader.add_css('office','a.offices-related-name::text')
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