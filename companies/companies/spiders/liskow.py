import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
from scrapy.selector import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'liskow'
    allowed_domains = ['liskow.com']
    start_urls = ['https://www.liskow.com/Team/Search?alpha=ALL']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('div.atty_name>a::attr(href)').getall()]
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
            page.goto(response.url)
            response = Selector(text=page.content())
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
        fullname_list = response.css('div.fullName::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_value('title',response.css('div.title1>div::text').get().split(',')[0])
        loader.add_css('email','a.atty_email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('div.education_list>div')]
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
        loader.add_value('image','https://www.liskow.com'+ response.css('img.people_summary_profilePhotos::attr(src)').get())
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.liskow.com/About')
        loader.add_value('office',response.css('div.title1>div::text').get().split(',')[1])
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


                