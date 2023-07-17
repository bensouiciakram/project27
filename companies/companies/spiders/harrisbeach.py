import scrapy
from scrapy import Request
from re import findall
from scrapy.item import Field 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
from scrapy.selector import Selector


class SkaddenSpider(scrapy.Spider):
    name = 'harrisbeach'
    allowed_domains = ['harrisbeach.com']
    start_urls = ['https://www.harrisbeach.com/bios/']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']




    def parse(self, response):
        with sync_playwright() as p :
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            page.wait_for_timeout(10000)
            urls_handles = page.query_selector_all('//a[contains(text(),"VIEW BIO")]')
            people_urls = [response.urljoin(url.get_attribute('href')) for url in urls_handles]
            self.logger.info('the extracted url : {}'.format(len(people_urls)))
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        url = response.url
        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            page.wait_for_selector('div.bio-name')
            response = Selector(text=page.content())
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',url)
        fullname_list = response.css('div.bio-name::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.bio-title::text')
        loader.add_value('email',response.css('div#social-email a::attr(href)').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[@id="education"]')]
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
        loader.add_css('image','div.bio-photo img::attr(src)')
        loader.add_xpath('bio','string(//div[@id="profileContainer"])')
        loader.add_value('firm_bio','https://www.harrisbeach.com/about/')
        loader.add_css('office','div.office-name a::text')
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


                