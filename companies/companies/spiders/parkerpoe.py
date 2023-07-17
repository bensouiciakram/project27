import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'parkerpoe'
    allowed_domains = ['parkerpoe.com']
    start_urls = set()

    def __init__(self):
        self.not_names = ['T.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        self.listing_template = 'https://www.parkerpoe.com/professionals#search/0/{}/0/0/0/0/0/0/0/0'
        with sync_playwright() as p :
            browser = p.firefox.launch()
            context = browser.new_context()
            page = context.new_page()
            for ch in 'abcdefghijklmnopqrstuvwxyz':
                page.goto(self.listing_template.format(ch.upper()))
                page.wait_for_timeout(10000)
                urls = page.query_selector_all('h4 a')
                self.start_urls = self.start_urls.union({'https://www.parkerpoe.com'+ url.get_attribute('href') for url in urls})
                print(self.start_urls)
                self.logger.info('the url extracted {}'.format(len(self.start_urls)))



    def parse(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h3)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h3/following-sibling::span/text()')
        loader.add_xpath('email','//a[contains(@href,"@parkerpoe.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h5[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_value('image',response.urljoin(response.css('div.content--overview img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="content--bio"])')
        loader.add_value('firm_bio','https://www.parkerpoe.com/aboutparkerpoe/aboutus')
        loader.add_css('office','div.contactoffice a::text')
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


                