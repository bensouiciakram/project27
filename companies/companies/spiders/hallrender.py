import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
from scrapy.selector import Selector


class SkaddenSpider(scrapy.Spider):
    name = 'hallrender'
    allowed_domains = ['hallrender.com']
    start_urls = ['https://www.hallrender.com/attorneys/']

    def __init__(self):
        self.not_names = ['H.','T.','J.D.','CISSP','N.','MLS(ASCP)CM','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']




    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.xpath('//p[@class="atty__title"]/ancestor::a/@href').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        url = response.url
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            response = Selector(text=page.content())
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
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
        loader.add_value('title',response.xpath('//h1/following-sibling::h2/text()').get().split('|')[0])
        loader.add_value('email',response.css('div.attorney-contact-buttons>a::attr(href)').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"EDU")]/following-sibling::div/p')]
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
        loader.add_css('image','div.attorney-headshot img::attr(src)')
        loader.add_value('bio',' '.join(response.xpath('//h3[contains(text(),"About")]/following-sibling::p').getall()))
        loader.add_value('firm_bio','https://www.hallrender.com/about-us/')
        loader.add_value('office',response.xpath('//h1/following-sibling::h2/text()').get().split('|')[1])
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


