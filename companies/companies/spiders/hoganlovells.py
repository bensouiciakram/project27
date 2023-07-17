import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from scrapy.selector import Selector
from time import sleep

class HoganlovellsSpider(scrapy.Spider):
    name = 'hoganlovells'
    allowed_domains = ['hoganlovells.com']
    start_urls = ['http://hoganlovells.com/']



    def __init__(self):
        self.people_template = 'https://www.hoganlovells.com/UpdatePeopleSearchResults?sortby=Relevance&pagenum={}'


    def start_requests(self):
        yield Request(
            self.people_template.format(1),
            callback = self.parse_people_listing,
            meta = {
                'page':1,
            }
        )
    
    def parse_people_listing(self, response):
        if not self.check_response(response) :
            return
        people_urls = ['https://www.hoganlovells.com' + url for url in response.css('h3 a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url ,
                callback = self.parse_individual
            )
        page = response.meta['page'] + 1
        yield Request(
            self.people_template.format(page),
            callback = self.parse_people_listing,
            meta = {
                'page': page,
            }
        )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        full_name_list = response.xpath('(//h1)[1]/text()').get().split(' ',1)
        loader.add_value('first_name',full_name_list[0])
        loader.add_value('last_name',full_name_list[-1])
        loader.add_value('email',response.xpath('//span[contains(text(),"Email")]/following-sibling::a/@title').get().split()[-1])
        loader.add_xpath('law_school','//div[@class="bio-portfolio"]/p[contains(text(),"law") or contains(text(),"Law")]/text()')
        loader.add_xpath('law_school_graduation_year','//div[@class="bio-portfolio"]/p[contains(text(),"law") or contains(text(),"Law")]/text()',re=r'\d+')
        loader.add_xpath('undergraduate_school','//div[@class="bio-portfolio"]/p[contains(text(),"Univ") or contains(text(),"univ")]/text()')
        loader.add_xpath('undergraduate_school_graduation_year','//div[@class="bio-portfolio"]/p[contains(text(),"Univ") or contains(text(),"univ")]/text()',re=r'\d+')
        loader.add_value('image','www.hoganlovells.com'+response.css('div.biography-photo img::attr(src)').get())
        loader.add_xpath('bio','string(//div[@class="intro"])')
        loader.add_xpath('title','(//div[@class="biography-card-text"]//p)[1]/text()')
        loader.add_value('firm_bio','https://www.hoganlovells.com/en/about-us')
        loader.add_xpath('office','//h1/following-sibling::p/a/text()')
        loader.add_value('firm','hoganlovells')
        yield loader.load_item()

    def check_response(self,response):
        return not 'No results found' in response.text