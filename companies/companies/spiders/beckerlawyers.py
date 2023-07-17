import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'beckerlawyers'
    allowed_domains = ['beckerlawyers.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        self.listing_template = 'https://beckerlawyers.com/professionals/?fwp_paged={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
            meta={
                'page':1
            }
        )

    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('h2.entry-title>a::attr(href)').getall()]
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
        loader.add_css('title','p.professionals-title b::text')
        loader.add_css('email','p.professionals-email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul[1]//ul/li')]
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
        loader.add_css('image','div.professionals-portrait::attr(style)')
        loader.add_xpath('bio','string(//div[@class="professionals-content"])')
        loader.add_value('firm_bio','https://beckerlawyers.com/about/')
        loader.add_css('office','div.location b::text')
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


                