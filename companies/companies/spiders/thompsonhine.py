import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright



class ThompsonhineSpider(scrapy.Spider):
    name = 'thompsonhine'
    allowed_domains = ['thompsonhine.com']

    def __init__(self):
        self.start_urls = []
        with sync_playwright() as p :
            self.run(p)

    def parse(self, response):
        script = response.xpath('//head/script/text()').get()
        regex = '"url":"(\S+?)"'
        people_urls = ['https://www.thompsonhine.com/'+url.replace('\\','') for url in set(findall(regex,script))]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h3/text()')
        loader.add_css('email','p.pageEmail a::text')
        educations_list = set([edu.xpath('string(.)').get() for edu in response.xpath('//ul[@class="education-list"]/li')])
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
        try:
            loader.add_value('image','https://www.thompsonhine.com' + response.css('div.sidebar-image img::attr(src)').get())
        except TypeError :
            loader.add_value('image','no image')
        loader.add_xpath('bio','string(//div[@id="Overview"])')
        loader.add_value('firm_bio','https://www.thompsonhine.com/about/')
        loader.add_xpath('office','string((//ul[@class="linkList contact information"]//p)[1])')
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


    def get_listing_urls(self,response):
        if 'tmp/cache/data/pnc_cache2' in response.url :
            self.start_urls.append(response.url)

    def run(self,p):
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_listing_urls)
        page.goto('https://www.thompsonhine.com/professionals/',timeout=60000)
        page.close()

