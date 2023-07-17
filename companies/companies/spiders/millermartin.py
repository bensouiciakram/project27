import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'millermartin'
    allowed_domains = ['millermartin.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Jr','Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        self.listing_template = 'https://www.millermartin.com/people/attorneys/?p={}'

    def start_requests(self):
        yield Request(
            self.listing_template.format(1)
        )


    def parse(self,response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages):
            yield Request(
                self.listing_template.format(page),
                callback= self.parse_individuals,
                dont_filter=True
            )

    def parse_individuals(self, response):
        people_divs = response.xpath('//div[@class="name"]/ancestor::div[2]')
        people_items = [(response.urljoin(div.css('div.name>a::attr(href)').get()),div.xpath('.//div[@class="name"]/ancestor::div[1]/following-sibling::div/text()').get()) for div in people_divs]
        for item in people_items :
            yield Request(
                item[0],
                callback =self.parse_individual,
                meta={
                    'title':item[1]
                }
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h2)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_value('title',response.meta['title'])
        loader.add_xpath('email','//h2/following-sibling::p[last()-1]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','div.biopage img::attr(src)')
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview")]/following-sibling::p)')
        loader.add_value('firm_bio','https://www.millermartin.com/about/our-firm/')
        loader.add_xpath('office','//h2/following-sibling::p[1]/text()')
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.xpath('string(//li[@class="page-item"][last()-1])').get())


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


                