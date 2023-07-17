import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response


class SkaddenSpider(scrapy.Spider):
    name = 'babstcalland'
    allowed_domains = ['babstcalland.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['A.A.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        self.listing_template = 'https://www.babstcalland.com/people/professional-search/page/{}/'

    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
            meta={
                'page':1
            }
        )


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('h3 a::attr(href)').getall()]
        if not people_urls :
            return 
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )
        page = response.meta['page'] + 1
        yield Request(
            self.listing_template.format(page),
            meta={
                'page':page
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
        loader.add_css('title','h4.attorney-spotlight-title::text')
        loader.add_css('email','h5.attorney-spotlight-email a::text')
        educations_list = [edu.get() for edu in response.xpath('//h5[contains(text(),"Education:")]/following-sibling::p/text()')]
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
        loader.add_xpath('image','//div[@class="show-print"]/following-sibling::img/@src')
        loader.add_xpath('bio','//h2/following-sibling::p/text()')
        loader.add_value('firm_bio','https://www.babstcalland.com/firm/about-babst-calland/')
        loader.add_value('office','')
        yield loader.load_item()


    def get_total_pages(self,response):
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


                