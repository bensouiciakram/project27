import scrapy
from scrapy import Request,FormRequest
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
import requests
from scrapy.shell import inspect_response
from scrapy.selector import Selector


class LwSpider(scrapy.Spider):
    name = 'lw'
    allowed_domains = ['lw.com']
    start_urls = ['http://lw.com/']

    formdata = {
        '__EVENTTARGET':'ctl00$ctl00$ContentPlaceHolder1$MainContentPlaceHolder$PagerControl2',
        '__EVENTARGUMENT':'1',
        '__VIEWSTATE':''
    }



    def __init__(self):
        self.people_template = 'https://www.lw.com/people?searchIndex={}'

    def start_requests(self):
        for ch in 'a':#bcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.people_template.format(ch.upper()),
                meta = {
                    'page':1
                }
            )

    def parse(self, response):
        scrapy_response = response
        page = response.meta['page']
        url = response.url
        if page  == 1 : 
            response = Selector(text=requests.get(response.url).text)
        else :
            self.formdata[ '__VIEWSTATE'] = str(page)
            response = Selector(text=requests.post(response.url,data=self.formdata).text)
        #inspect_response(response,self)
        if not self.check_response(response) :
            self.logger.info('\n no results on {} \n'.format(url.split('=')[-1]))
            return 

        people_urls = response.css('div.tileName a::attr(href)').getall()
        print(poeple_urls)
        for link in people_urls : 
            yield Request(
                'http://lw.com' + link,
                callback = self.parse_individual
            )
        page += 1
        viewstate = response.css('input#__VIEWSTATE::attr(value)').get()
        yield FormRequest(
            url,
            formdata= self.formdata.update(
                {
                    '__EVENTARGUMENT' : str(page),
                    '__VIEWSTATE' : viewstate
                }
            ),
            dont_filter = True,
            meta ={
                'page' :page
            }
        )

    def parse_individual(self,response):

        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)

        name_list = response.css('h1::text').get().split()
        loader.add_value('first_name',name_list[0])
        loader.add_value('last_name',name_list[1])

        loader.add_css('title','span.bioTitle::text')
        loader.add_xpath('email','//span[@class="addressLegend"]/following-sibling::a/text()')
        loader.add_xpath('law_school','//ul[@id="AttorneyMetaData"]//li[contains(text(),"Law") or contains(text(),"law")]/text()')
        loader.add_value('law_school_graduation_year',self.get_law_schools_years(response))
        loader.add_xpath('undergraduate_school','//ul[@id="AttorneyMetaData"]//li[contains(text(),"Univ") or contains(text(),"univ")]/text()')
        loader.add_value('undergraduate_school_graduation_year',self.get_undergraduate_schools_years(response))
        loader.add_value('image','http://lw.com' + response.css('div#BioPhotoPanel img::attr(src)').get())
        loader.add_xpath('bio','string(//div[@id="BioContent"])')
        loader.add_value('firm_bio','https://www.lw.com/AboutUs')
        loader.add_css('office','span#ContentPlaceHolder1_HeadingPlaceHolder_OfficesLabel a::text')
        yield loader.load_item()


    def check_response(self,response):
        check_tag = response.xpath('//h5//text()').get()
        if not check_tag :
            return True
        return not '0 results' in check_tag

    def get_law_schools_years(self,response):
        schools = response.xpath('//ul[@id="AttorneyMetaData"]//li[contains(text(),"Law") or contains(text(),"law")]/text()').getall()
        return [school.split(',')[-1] for school in schools]

    def get_undergraduate_schools_years(self,response):
        schools = response.xpath('//ul[@id="AttorneyMetaData"]//li[contains(text(),"Univ") or contains(text(),"univ")]/text()').getall()
        return [school.split(',')[-1] for school in schools]