import scrapy
import requests
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from scrapy import Request
from re import findall
from playwright.sync_api import sync_playwright
from scrapy.shell import inspect_response

class DlapiperSpider(scrapy.Spider):
    name = 'dlapiper'
    allowed_domains = ['dlapiper.com']
    start_urls = ['https://dlapiper.com/']

    def __init__(self):
        self.start_urls = set()
        with sync_playwright() as p : 
            self.run(p)

    # def start_requests(self):
    #     for url in self.start_urls : 
    #         yield Request(
    #             self.normalize_url(url)
    #         )


    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.media-body h2::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_css('firm','span.h::text')
        loader.add_css('title','div.media-body h3::text')
        loader.add_css('email','a.attyemail::text')
        img_url =response.css('div.media-img img::attr(src)').get()
        loader.add_value('image',response.urljoin(img_url))
        loader.add_xpath('bio','string(//div[@class="page-overview rich-text"])')
        loader.add_value('firm_bio','https://www.dlapiper.com/en/us/aboutus/')
        loader.add_css('office','address p a::text')
        loader.add_css('bar','div.media-body h4::text')
        yield Request(
            response.url + '?tab=credentials',
            callback = self.parse_schools,
            meta = {
                'loader':loader
            }
        )

    def parse_schools(self,response):
        loader = response.meta['loader']
        law_school = response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul/li[contains(text(),"Law") or contains(text(),"law")]/text()').get()
        loader.add_value('law_school',law_school)
        try : 
            loader.add_value('law_school_graduation_year',findall('\d\d\d\d',law_school)[0])
        except IndexError : 
            pass
        except TypeError :
            pass
        undergraduate_school = response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul/li[(contains(text(),"univ") or contains(text(),"Univ") or contains(text(),"coll") or contains(text(),"Coll")) and not(contains(text(),"Law")) and not(contains(text(),"law"))]/text()').get()
        loader.add_value('undergraduate_school',undergraduate_school)
        try : 
            loader.add_value('undergraduate_school_graduation_year',findall('\d\d\d\d',undergraduate_school)[0])
        except IndexError : 
            pass
        except TypeError :
            pass
        yield loader.load_item()



    def get_data(self,response):
        if '?sitecoreItemUri' in response.url :
            people_urls = {individual['printableUri'] for individual in response.json()['results']}
            self.start_urls = self.start_urls.union(people_urls)
            self.logger.info('{} urls collected , total {}'.format(len(people_urls),len(self.start_urls)))
            return response.json()    


    def run(self,p):
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.on('response',self.get_data)
        page.goto('https://www.dlapiper.com/en/us/people/#sort=relevancy')
        page.click('//a[contains(text(),"100")]')
        page.wait_for_timeout(5000)
        total_pages = self.get_total(page)//100
        for page_id in range(1,total_pages + 1) :
            page.goto('https://www.dlapiper.com/en/us/people/#first={}&sort=relevancy'.format(100*(page_id - 1)))
            page.wait_for_timeout(5000)
            



    def get_total(self,page):
        return int(page.query_selector('//span[@class="CoveoQuerySummary"]//span[3]').inner_text().replace(',',''))


    # def normalize_url(self,url):
    #     split_list = url.split('/')
    #     return '/'.join(split_list[:4]) + '/africa/' + '/'.join(split_list[4:])