import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class JonesdaySpider(scrapy.Spider):
    name = 'jonesday'
    allowed_domains = ['jonesday.com']
    start_urls = ['http://jonesday.com/']

    def __init__(self):
        self.listing_template = 'https://www.jonesday.com/en/lawyers#first={}&sort=%40fieldz95xalphasort%20ascending&f:@facetz95xalpha={}'
        self.start_urls = set()
        with sync_playwright() as p : 
            self.run(p)


            
    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        loader.add_xpath('first_name','//span[@class="profile__name"]/text()')
        loader.add_xpath('last_name','//span[@class="profile__name profile__name--em"]/text()')
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::h2/span/text()')
        loader.add_value('email',response.xpath('//li[@class="profile__tool"][1]/a/@href').get().replace('mailto:',''))
        img_url =response.urljoin(response.css('figure img::attr(src)').get())
        loader.add_value('image',img_url)
        loader.add_xpath('bio','string(//section[@aria-label="Overview"])')
        loader.add_value('firm_bio','https://www.jonesday.com/en/firm?tab=overview')
        loader.add_css('office','span.profile__metatitle::text')
        educations_list = response.xpath('string(//h3[descendant::button[contains(text(),"Education")]]/following-sibling::div//li)').get().split(';')
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
        #loader.add_css('bar','div.media-body h4::text')
        yield loader.load_item()


    def get_data(self,response):
        if '?sitecoreItemUri' in response.url :
            people_urls = {individual['printableUri'] for individual in response.json()['results']}
            self.start_urls = self.start_urls.union(people_urls)
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            return response.json()    


    def run(self,p):
        browser = p.chromium.launch()#headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            page.goto(self.listing_template.format(0,ch.upper()),wait_until="networkidle")
            page.wait_for_timeout(5000)
            total_pages = self.get_total_page(page)
            for page_id in range(total_pages) :
                page.goto(self.listing_template.format(20*page_id,ch.upper()),wait_until="networkidle")
                page.wait_for_timeout(5000)

    def get_total_page(self,page):
        return ceil(int(page.query_selector('(//span[@class="coveo-highlight"])[last()]').inner_text())/20)

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