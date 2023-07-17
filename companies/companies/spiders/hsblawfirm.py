import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response


class SkaddenSpider(scrapy.Spider):
    name = 'hsblawfirm'
    allowed_domains = ['hsblawfirm.com']
    start_urls = ['https://www.hsblawfirm.com/Attorneys']

    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('a.attorneyBoxAction::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h1)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2].replace(',',''))
        else :
            loader.add_value('last_name', fullname_list[-1].replace(',',''))
        loader.add_value('firm',self.name)
        loader.add_value('title',response.xpath('//h1/following-sibling::div/div/text()').get().replace('|','').strip())
        loader.add_value('email',response.css('a.email::attr(href)').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('(//div[@class="attorneyDetailHeader"]/following-sibling::ul)[1]/li')]
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
        loader.add_value('image',response.urljoin(response.css('div.attorneyPrint>div').re('url\(([\s\S]+)\)')[0]))
        loader.add_xpath('bio','string(//main[@class="attorneyDetail"])')
        loader.add_value('firm_bio','https://www.hsblawfirm.com/About')
        loader.add_css('office','a#hypAttorneyLocation::text')
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


                