import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class KnobbeSpider(scrapy.Spider):
    name = 'knobbe'
    allowed_domains = ['knobbe.com']
    start_urls = ['http://knobbe.com/']

    def __init__(self):
        self.listing_template = 'https://www.knobbe.com/attorneys?sort_by=position_weight&page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            meta= {
                'page':0
            }
        )

    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('div.co-chair-item__name a::attr(href)').getall()]
        page = response.meta['page']
        if not people_urls : 
            return 
        else :
            page += 1 
            yield Request(
                self.listing_template.format(page),
                meta= {
                    'page':page
                }
            )
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.attorney-header__info--position::text')
        loader.add_xpath('email','//a[contains(@href,"mailto")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/following-sibling::div[1]/div')]
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
        loader.add_value('image',response.urljoin(response.css('div.attorney-header__image::attr(style)').re('\((\S+)\)')[0]))
        loader.add_xpath('bio','string(//div[contains(@class,"field field--name-body")])')
        loader.add_value('firm_bio','https://www.knobbe.com/about-us')
        loader.add_css('office','div.attorney-header__info--office a::text')
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