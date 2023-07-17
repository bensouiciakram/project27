import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'sewkis'
    allowed_domains = ['sewkis.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Y.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.sewkis.com/people/')
            while True :
                try :
                    page.wait_for_selector('//button[contains(text(),"Load more")]',timeout=5000)
                    page.click('//button[contains(text(),"Load more")]')
                except :
                    break
            self.start_urls += [handle.get_attribute('href') for handle in page.query_selector_all('h6 a')]
            self.logger.info('the extracted urls : {}'.format(len(self.start_urls)))


    def parse(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1.hero__title::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','p.hero__subtitle--content::text')
        loader.add_xpath('email','(//a[contains(@href,"@sewkis.com")])[2]/text()')
        # educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('')]
        # try :
        #     law_school , year = self.get_law_school(educations_list)
        #     loader.add_value('law_school',law_school)
        #     loader.add_value('law_school_graduation_year',year)
        # except TypeError : 
        #     pass 
        # try : 
        #     undergraduate_school, year = self.get_undergraduate_school(educations_list)
        #     loader.add_value('undergraduate_school',undergraduate_school)
        #     loader.add_value('undergraduate_school_graduation_year',year)
        # except TypeError :
        #     pass
        loader.add_css('image','img.hero__images-inside::attr(src)')
        loader.add_xpath('bio','string(//div[contains(@class,"entry__attorney-biography")])')
        loader.add_value('firm_bio','https://www.sewkis.com/#about')
        loader.add_xpath('office','//p[@class="hero__subtitle--content"]/following-sibling::div//p[1]/text()[2]')
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


                
