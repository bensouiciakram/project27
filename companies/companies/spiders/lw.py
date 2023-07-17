import scrapy
from scrapy import FormRequest,Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall

class LwSpider(scrapy.Spider):
    name = 'lw'
    allowed_domains = ['lw.com']
    start_urls = []


    def __init__(self):
        self.listing_template = 'https://www.lw.com/people?searchIndex={}'
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.index = 0

    def start_requests(self):
        yield Request(
                self.listing_template.format(self.alphabet[self.index].upper()),
                meta= {
                    'page':1,
                }
            )

    def parse(self, response):
        page = response.meta['page']
        people_urls = [response.urljoin(url) for url in response.css('div.tileName a::attr(href)').getall()]
        if not people_urls : 
            if self.alphabet[self.index] == 'z' :
                return
            else : 
                self.index += 1
                page = 0

        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual,
            )
        
        page +=1
        if page == 1 :
            yield Request(
                self.listing_template.format(self.alphabet[self.index].upper()),
                meta= {
                    'page':1
                }
            )
        else : 
            viewstate =  response.css('input#__VIEWSTATE::attr(value)').get()
            formdata = {
                '__VIEWSTATE':viewstate,
                '__EVENTTARGET':'ctl00$ctl00$ContentPlaceHolder1$MainContentPlaceHolder$PagerControl2',
                '__EVENTARGUMENT':str(page)
            }

            yield FormRequest(
                self.listing_template.format(self.alphabet[self.index].upper()),
                formdata= formdata,
                meta = {
                    'page': page,
                    'ch': response.url.split('=')[-1]
                }
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        name_list = response.css('h1::text').get().split()
        loader.add_value('first_name',name_list[0])
        loader.add_value('last_name',name_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.bioTitle::text')
        loader.add_xpath('email','//span[@class="addressLegend"]/following-sibling::a/text()')

        try:
            loader.add_value('image','http://lw.com' + response.css('div#BioPhotoPanel img::attr(src)').get())
        except TypeError :
            pass
        loader.add_xpath('bio','string(//div[@id="BioContent"])')
        loader.add_value('firm_bio','https://www.lw.com/AboutUs')
        loader.add_css('office','span#ContentPlaceHolder1_HeadingPlaceHolder_OfficesLabel a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//span[contains(text(),"Education")]/ancestor::div[1]/following-sibling::ul/li')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass
        try  :
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError : 
            pass
        yield loader.load_item()

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