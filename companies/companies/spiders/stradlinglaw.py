import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response


class SkaddenSpider(scrapy.Spider):
    name = 'stradlinglaw'
    allowed_domains = ['stradlinglaw.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        self.listing_template = 'https://www.stradlinglaw.com/professionals/index.html?f={}'

    def start_requests(self):
        yield Request(
            self.listing_template.format(0)
        )


    def parse(self,response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(20*page),
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self, response):
        people_urls = [response.urljoin(url) for url in response.css('dt>a::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h1)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.rte-title-mode::text')
        loader.add_xpath('email','//a[contains(@href,"@stradlinglaw.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/ancestor::div[2]/following-sibling::div//li')]
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
        loader.add_xpath('bio','string(//div[contains(@class,"l-main-column-item")])')
        loader.add_value('firm_bio','https://www.stradlinglaw.com/our-firm.html')
        loader.add_xpath('office','(//span[@class="rte-title-mode"]/text())[2]')
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.xpath('(//a[@role="button"]/text())[last()]').get())

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


                