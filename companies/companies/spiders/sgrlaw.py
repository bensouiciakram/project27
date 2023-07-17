import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SgrlawSpider(scrapy.Spider):
    name = 'sgrlaw'
    allowed_domains = ['sgrlaw.com']
    start_urls = ['https://www.sgrlaw.com/people/?sq=']


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def parse(self, response):
        people_urls = response.css('h3 a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.seo-attorney-jobtitle::text')
        loader.add_value('email',response.css('a.email::attr(href)').get().replace('mailto:',''))
        loader.add_xpath('law_school','(//strong[contains(text(),"Law School")]/ancestor::span/following-sibling::ul)[1]/li/text()')
        loader.add_xpath('law_school_graduation_year','(//strong[contains(text(),"Law School")]/ancestor::span/following-sibling::ul)[1]/li/text()',re='\d\d\d\d')
        loader.add_xpath('undergraduate_school','(//strong[contains(text(),"Undergraduate")]/ancestor::span/following-sibling::ul)[1]/li/text()')
        loader.add_xpath('undergraduate_school_graduation_year','(//strong[contains(text(),"Undergraduate")]/ancestor::span/following-sibling::ul)[1]/li/text()',re='\d\d\d\d')
        loader.add_css('image','div.c-attorney__thumbnail img::attr(src)')
        loader.add_xpath('bio','string(//a[contains(text(),"Full Bio")]/ancestor::h2/following-sibling::div[1])')
        loader.add_value('firm_bio','https://www.sgrlaw.com/about-sgr/')
        loader.add_css('office','a.c-attorney__location::text')
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