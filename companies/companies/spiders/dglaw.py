import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'dglaw'
    allowed_domains = ['dglaw.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome',headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.dglaw.com/people')
            for _ in range(10):
                page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight);')
                try: 
                    page.click('//button[contains(text(),"More")]',timeout=3000)
                except :
                    pass
                page.wait_for_timeout(3000)
            self.start_urls = [handle.get_attribute('href') for handle in page.query_selector_all('h2.entry-title>a')]
        self.logger.info('extracted urls : {}'.format(len(self.start_urls)))


    def parse(self,response):
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
        loader.add_css('title','p.positions>span::text')
        loader.add_css('email','a.email>span::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::div/ul/li')]
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
        loader.add_xpath('image','//h1/ancestor::div[1]/@style')
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.dglaw.com/about-us/overview/')
        loader.add_xpath('office','string(//h5[contains(text(),"Bar Admissions")]/following-sibling::ul/li)')
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


                