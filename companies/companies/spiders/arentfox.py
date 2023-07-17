import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class ArentfoxSpider(scrapy.Spider):
    name = 'arentfox'
    allowed_domains = ['arentfox.com']
    start_urls = ['http://arentfox.com/']

    def __init__(self):
        self.listing_template = 'https://www.arentfox.com/attorneys?page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0)
        )

    def parse(self, response):
        total_pages = self.get_total(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.css('span.field-content a::attr(href)').getall()]
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
        loader.add_xpath('title','//div[@class="field field--name-field-job-title field--type-entity-reference field--label-hidden field__item"]/text()')
        loader.add_value('email',response.xpath('//a[contains(text(),"Contact Me")]/@href').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//span[contains(text(),"Education")]//following-sibling::div//div[@class="field__item"]')]
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
        loader.add_value('image',response.urljoin(response.xpath('(//div[@class="field field--name-field-image field--type-image field--label-hidden field__item"]/img)[1]/@src').get()))
        loader.add_xpath('bio','string((//div[@class="clearfix text-formatted field field--name-body field--type-text-with-summary field--label-hidden field__item"])[1])')
        loader.add_value('firm_bio','https://www.arentfox.com/about')
        loader.add_xpath('office','string(//span[contains(text(),"Offices")]/following-sibling::div)')
        yield loader.load_item()


    def get_total(self,response):
        return int(response.xpath('//li[@class="pager__item pager__item--last"]/a/@href').get().split('=')[-1])


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