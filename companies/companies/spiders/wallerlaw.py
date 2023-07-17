import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright

class WallerlawSpider(scrapy.Spider):
    name = 'wallerlaw'
    allowed_domains = ['wallerlaw.com']
    start_urls = ['http://wallerlaw.com/']
    headers= {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    body = 'pagination={}'

    def __init__(self):
        self.start_urls = []
        self.listing_template =  'https://www.wallerlaw.com/our-people?page={}'
        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            for ch in 'abcdefghijklmnopqrstuvwxyz' :
                page.goto(self.listing_template.format(ch.upper()))
                page.wait_for_timeout(3000)
                #page.wait_for_selector('a.nostyle')
                self.start_urls += ['https://www.wallerlaw.com'+ handle.get_attribute('href')[1:] for handle in page.query_selector_all('a.nostyle')[1:]]
                self.logger.info('total urls collected {}'.format(len(self.start_urls)))
        

    def start_requests(self):
        for url in self.start_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = [name.title() for name in response.xpath('//h1/text()').get().split()]
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2.hero_sub_txt::text')
        loader.add_value('email',response.xpath('(//a[contains(@href,"@wallerlaw.com")])[1]/@href').get().replace('mailto:',''))
        educations_list = [self.get_education_text(li) for li in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_xpath('image','//script[contains(text(),"background-image")]',re = "url\('(\S+?)'\)")
        loader.add_xpath('bio','string(//div[@id="full_bio"]/ancestor::div[1])')
        loader.add_value('firm_bio','https://www.wallerlaw.com/about-waller')
        loader.add_xpath('office','string(//h2[contains(text(),"Contact Info")]/following-sibling::div//p[1])')
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

    def get_education_text(self,li) :
        return ' '.join([sel.get() for sel in li.xpath('./text()')])