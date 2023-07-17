import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 


class SkaddenSpider(scrapy.Spider):
    name = 'susmangodfrey'
    allowed_domains = ['susmangodfrey.com']
    start_urls = set()

    def __init__(self):
        self.not_names = ['(1941','-','2020)','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]
        with sync_playwright() as p :
            browser = p.chromium.launch(channel='chrome')#,headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://www.susmangodfrey.com/attorneys/')
            while True :
                try:
                    page.click('a#top-next',timeout=5000)
                    self.start_urls = self.start_urls.union({handle.get_attribute('href') for handle in page.query_selector_all('//a[descendant::h2]')})
                except :
                    break
            print(len(self.start_urls))


    def parse(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        try :
            fullname_list = response.css('div.attorney-name::text').get().split()
        except AttributeError :
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
        loader.add_css('title','div.attorney-title::text')
        if not loader._values.get('title'):
            loader.add_xpath('title','//div[@class="attorney-name"]/following-sibling::p/text()')
        try:
            loader.add_value('email',response.xpath('//a[contains(text(),"Email")]/@href').get().replace('mailto:',''))
        except AttributeError :
            pass
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//span[contains(text(),"Education")]/following-sibling::div//li')]
        if not educations_list :
            educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//strong[contains(text(),"Education:")]/ancestor::div[1]/following-sibling::p')]
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
        loader.add_css('image','img.profile-pic::attr(src)')
        if not loader._values.get('image') :
            loader.add_css('image','img.imgPaddingRight::attr(src)')
        loader.add_xpath('bio','string(//div[@id="overview"])')
        loader.add_value('firm_bio','https://www.susmangodfrey.com/about-us/')
        loader.add_css('office','span.heading::text')
        if not loader._values.get('office'):
            loader.add_css('office','div.cityNames>p::text')
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


                