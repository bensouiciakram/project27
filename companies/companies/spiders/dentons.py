import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from scrapy.selector import Selector 



class DentonsSpider(scrapy.Spider):
    name = 'dentons'
    allowed_domains = ['dentons.com']
    start_urls = []


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome',headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.dentons.com/en/our-professionals')
            page.query_selector('button#onetrust-accept-btn-handler').click()
            for _ in range(30):
                page.wait_for_selector('//button[contains(text(),"Load more professionals")]')
                page.click('//button[contains(text(),"Load more professionals")]',timeout=60000)
            urls = page.query_selector_all('a.col-photo')
            self.start_urls = [handle.get_attribute('href') for handle in urls ]
            self.logger.info('the extracted urls : {} '.format(len(self.start_urls)))


    def parse(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        try :
            fullname_list = response.xpath('//h1/text()').get().split()
        except : 
            fullname_list = response.xpath('//h2/text()').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::small/text()')
        try:
            loader.add_value('email',response.css('a.email::attr(rel)').get().replace('mailto:',''))
        except AttributeError :
            try:
                loader.add_value('email', response.xpath('//a[contains(@href,"mailto")]/@href').get().replace('mailto:',''))
            except AttributeError :
                pass
        educations_list = [edu.xpath('string(.)').get() for edu in response.css('div.education p')]
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
        loader.add_value('image',response.urljoin(response.xpath('(//figure/img[@title])[last()]/@src').get()))
        loader.add_xpath('bio','string(//div[contains(@class,"About")])')
        loader.add_value('firm_bio','https://www.dentons.com/en/')
        loader.add_css('office','div.bio-contact b::text')
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


                