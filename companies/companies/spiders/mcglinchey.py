import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import re 
from math import ceil
from playwright._impl._api_types import TimeoutError
from playwright.sync_api import sync_playwright


class SkaddenSpider(scrapy.Spider):
    name = 'mcglinchey'
    allowed_domains = ['mcglinchey.com']
    start_urls = set()

    def __init__(self):
        self.not_names = ['T.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']
        self.listing_url = 'https://www.mcglinchey.com/people/?s=&post_type=poa_person'
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome',headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.listing_url)
            page.wait_for_timeout(5000)
            with page.expect_response(re.compile(r"^https://25otrj4gi7-dsn.algolia.net/1/indexes"),timeout=60000) as response_info:
                page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight);')
                response = response_info.value
                total_urls  = response.json()['results'][0]['nbHits']

            total_pages = ceil(total_urls/16)
            for page_id in range(1,total_pages +1):
                if page_id % 3 == 1 :
                    page.goto('https://www.mcglinchey.com/people/?page={}'.format(page_id))
                    page.wait_for_timeout(5000)
                page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight);')
                page.wait_for_timeout(5000)
                self.start_urls = self.start_urls.union({handle.get_attribute('href') for handle in page.query_selector_all('h2.entry-title>a')})
                self.logger.info('the extracted urls : {}'.format(len(self.start_urls)))



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
        loader.add_css('title','span.position::text')
        loader.add_css('email','a.email span::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//section[@aria-label="Education"]//li')]
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
        loader.add_css('image','figure img::attr(src)')
        loader.add_xpath('bio','string(//div[@itemprop="description"])')
        loader.add_value('firm_bio','https://www.mcglinchey.com/firm/about-us/')
        loader.add_css('office','a.office-link::text')
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


                