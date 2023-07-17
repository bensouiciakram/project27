import scrapy
from playwright.sync_api import sync_playwright
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall


class KirklandSpider(scrapy.Spider):
    name = 'kirkland'
    allowed_domains = ['kirkland.com']
    start_urls = ['http://kirkland.com/']

    def __init__(self):
        self.start_urls = set()
        self.listing_template = 'https://www.kirkland.com/lawyers?letter={}&page={}'
        self.total_pages = 0
        with sync_playwright() as p : 
            self.run(p)


    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('span.profile-heading__name-label::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_css('firm',self.name)
        loader.add_xpath('title','//span[@class="profile-heading__position "]/text()')
        loader.add_xpath('email','//a[@class="profile-heading__email"]/text()')
        img_url =response.urljoin(response.css('img.profile-heading__snapshot::attr(src)').get())
        loader.add_value('image',img_url)
        loader.add_xpath('bio','string((//div[@class="rte"])[1])')
        loader.add_value('firm_bio','https://www.kirkland.com/content/about-kirkland')
        loader.add_css('office','a.profile-heading__location-link::text')
        educations_list = [ edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul//li')]
        try: 
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try:
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError: 
            pass
        yield loader.load_item()


    def get_data(self,response):
        if 'ProfessionalsApi/Lawyers' in response.url :
            people_urls = {'https://www.kirkland.com/' + individual['Url'] for individual in response.json()['Results']}
            self.start_urls = self.start_urls.union(people_urls)
            self.total_pages = response.json()['TotalSearchResults']//10
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            return response.json()    


    def run(self,p):
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            page.goto(self.listing_template.format(ch.upper(),0))
            page.wait_for_timeout(5000)
            total_pages = self.total_pages
            page.goto(self.listing_template.format(ch.upper(),total_pages))
            page.wait_for_timeout(5000)


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