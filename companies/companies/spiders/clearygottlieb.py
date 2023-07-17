import scrapy
from playwright.sync_api import sync_playwright
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall

class ClearygottliebSpider(scrapy.Spider):
    name = 'clearygottlieb'
    allowed_domains = ['clearygottlieb.com']
    start_urls = ['http://clearygottlieb.com/']

    def __init__(self):
        self.total_urls = 0
        self.start_urls = set()
        with sync_playwright() as p :
            self.run(p)


    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2.person-info__position::text')
        loader.add_css('email','a.contact-block__email::text')
        educations_list =  [edu.xpath('string(.)').get().strip() for edu in response.xpath('//h3[contains(text(),"Education")]/ancestor::header/following-sibling::div//li')]
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
        loader.add_value('firm_bio','https://www.clearygottlieb.com/about-us/who-we-are')
        loader.add_xpath('bio','string(//section[@class="content-section narrative section-expandable--showfade"])')
        loader.add_css('office','h4.location__city a::text')
        yield loader.load_item()


    def get_data(self,response):
        if 'api/sitecore/GlobalSearch' in response.url :
            people_urls = {'http://clearygottlieb.com' + individual['ItemUrl'] for individual in response.json()[0]['Results']}
            self.start_urls = self.start_urls.union(people_urls)
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            self.total_urls = response.json()[0]['TotalResultsNumber']
            return response.json()    


    def run(self,p):
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        page.goto('https://www.clearygottlieb.com/professionals')
        page.wait_for_timeout(3000)
        while len(self.start_urls) < self.total_urls : 
            page.query_selector('button.search-load-more__btn').click()
            page.wait_for_timeout(3000)


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