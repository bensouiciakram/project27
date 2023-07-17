import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from math import ceil 
from scrapy.selector import Selector
from playwright.sync_api import sync_playwright

class KramerlevinSpider(scrapy.Spider):
    name = 'kramerlevin'
    allowed_domains = ['kramerlevin.com']
    start_urls = ['http://kramerlevin.com/']

    def __init__(self):
        self.listing_template = 'https://www.kramerlevin.com/_site/search?v=attorney&view_more=true&html=true&s=100&sb=attorney&f={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0)
        )

    def parse(self, response):
        total_pages = self.get_total(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(100*page),
                callback = self.parse_individuals ,
                dont_filter = True
            )


    def parse_individuals(self,response):
        selector = Selector(text = response.json()['rendered_view'])
        people_urls = [response.urljoin(url) for url in selector.xpath('//li[@class="attorney-info__item attorney-info__item--name"]/a/@href').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//li[@class="attorney-info__title-block"]//li[1]/text()')
        with sync_playwright() as p : 
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            loader.add_value('email',page.query_selector('a.attorney-info__email-link').inner_text())
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','img.attorney-header__photo::attr(src)')
        loader.add_xpath('bio','string((//div[@class="page-attorney__content-section"])[1])')
        loader.add_value('firm_bio','https://www.kramerlevin.com/en/about-us/')
        loader.add_xpath('office','//li[@class="attorney-info__title-block"]//li[2]/text()')
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


    def get_total(self,response):
        return ceil(response.json()['totals']['ALL']/100)