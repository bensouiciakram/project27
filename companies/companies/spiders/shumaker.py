import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response
import pickle


class ShumakerSpider(scrapy.Spider):
    name = 'shumaker'
    allowed_domains = ['shumaker.com']
    start_urls = ['http://shumaker.com/']

    body = 'Action=GetProfessionals&alph=&keyword=&firstName=&lastName=&title=&officeId=&industryId=&practiceId=&barAdmission=&education=&language=&pageNumber={}'

    headers = {
        "authority": "www.shumaker.com",
        "sec-ch-ua": "\"Google Chrome\";v=\"93\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"93\"",
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-mod-sbb-ctype": "xhr",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "x-requested-with": "XMLHttpRequest",
        "sec-ch-ua-platform": "\"Linux\"",
        "origin": "https://www.shumaker.com",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.shumaker.com/professionals",
        "accept-language": "en-US,en;q=0.9"
    }

    def __init__(self):
        self.posting_url = 'https://www.shumaker.com/Templates/AjaxHandlers/ProfessionalListing.ashx'
        self.urls = set()

    def start_requests(self):
        yield Request(
            self.posting_url,
            method='POST',
            callback=self.parse_individuals,
            headers=self.headers,
            body = self.body.format(1),
            meta={
                'page':0
            }
        )

    def parse_individuals(self,response):
        try :
            people_urls = ['http://shumaker.com'+item['DisplayPath'] for item in response.json()]
            pickle.dump(people_urls,open('urls.pkl','wb'))
        except : 
            inspect_response(response,self)
        if not people_urls :
            return

        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )
        page = response.meta['page'] + 1
        yield Request(
            self.posting_url,
            method='POST',
            headers=self.headers,
            body = self.body.format(page),
            meta={
                'page':page
            }
        )
            
    def parse_individual(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        with sync_playwright() as p :
            loader.add_value('url',response.url)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            fullname_list = page.query_selector('//h1').inner_text().split()
            loader.add_value('first_name',fullname_list[0])
            loader.add_value('last_name',fullname_list[-1])
            loader.add_value('firm',self.name)
            loader.add_value('title',page.query_selector('h2.page-head-subtitle').inner_text())
            loader.add_value('email',page.query_selector('//a[contains(@href,"mailto")]').inner_text())
            educations_list = [edu.query_selector('string(.)').inner_text() for edu in page.query_selector_all('(//div[@id="Education"])[2]//li')]
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
            loader.add_value('image',response.urljoin(page.query_selector('div.bio img').get_attribute('src')))
            loader.add_value('bio',page.query_selector('string(//div[@id="Overview"])').inner_text())
            loader.add_value('firm_bio','https://www.shumaker.com/about-shumaker')
            loader.add_value('office',page.query_selector('(//div[@class="card"])[1]/div[last()]/a').inner_text())
        yield loader.load_item()


    # def get_data(self,response):
    #     if '/AjaxHandlers/ProfessionalListing.ashx' in response.url :
    #         people_urls = {'https://www.shumaker.com' + individual['DisplayPath'] for individual in response.json()}
    #         self.start_urls = self.start_urls.union(people_urls)
    #         self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
    #         return response.json()    

        
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