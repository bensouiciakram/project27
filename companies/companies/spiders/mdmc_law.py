import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright._impl._api_types import TimeoutError
import pickle



class MdmcLawSpider(scrapy.Spider):
    name = 'mdmc_law'
    allowed_domains = ['mdmc-law.com']
    start_urls = ['http://mdmc-law.com/']

    def __init__(self):
        self.listing_template = ''
        self.start_urls = set()
        self.items = []
        with sync_playwright() as p : 
            self.run(p)
        pickle.dump(self.items,open('item.pkl','wb'))


    def start_requests(self):
        for item in self.items :
            yield Request(
                item[0],
                meta={
                    'email':item[1]
                }
            )

            
    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1 span::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','string(//div[@class="bio-col-header"]/div[1])')
        loader.add_value('email',response.meta['email'])
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::div/div')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try: 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError : 
            pass

        loader.add_value('image',response.urljoin(response.xpath('//picture/img/@src').get()))
        loader.add_xpath('bio','string(//div[@class="col-content-desktop"])')
        loader.add_value('firm_bio','https://www.mdmc-law.com/about')
        loader.add_xpath('office','string(//div[contains(@class,"field field--name-field-title")])')
        yield loader.load_item()


    # def get_data(self,response):
    #     if 'ajax?_wrapper_format=drupal_ajax' in response.url :
    #         people_urls = {individual['printableUri'] for individual in response.json()['results']}
    #         self.start_urls = self.start_urls.union(people_urls)
    #         self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
    #         return response.json()    


    def run(self,p):
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        #page.on('response',self.get_data)
        page.goto('https://www.mdmc-law.com/attorneys',timeout=60000)
        page.wait_for_selector('a.bio-title')
        handles = page.query_selector_all('a.bio-title')
        self.items += [(self.get_url(handle),self.get_email(handle)) for handle in handles]
        self.logger.info('total {}'.format(len(self.items)))
        total_pages = self.get_total_pages(page)
        for page_id in range(1,total_pages):
            try :
                page.wait_for_selector('a[rel="next"]')
                page.click('a[rel="next"]',timeout=60000)
            except TimeoutError :
                continue
            page.wait_for_timeout(3000)
            page.wait_for_selector('a.bio-title')
            handles = page.query_selector_all('a.bio-title')
            self.items += [(self.get_url(handle),self.get_email(handle)) for handle in handles]
            self.logger.info('total {}'.format(len(self.items)))


    def get_total_pages(self,page):
        return ceil(max([int(number) for number in findall('\d+',page.query_selector('div.view-header__results').inner_text())])/20)
        
    
    def get_url(self,handle):
        return 'https://www.mdmc-law.com'+handle.get_attribute('href')
    

    def get_email(self,handle):
        return handle.query_selector('//following-sibling::div[1]//a').get_attribute('href').replace('mailto:','')


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