import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class MichaelbestSpider(scrapy.Spider):
    name = 'michaelbest'
    allowed_domains = ['michaelbest.com']
    start_urls = ['https://www.michaelbest.com/webportal/serveContent.v?src=ajax-website-search-result-lazy-load&guid=3c4f121990870c4d68857df56eeb9cf4:37003:33101/people&page=1&hitsPerPage=500&urlPrefix=../&totalPages=57&showIcons=true']

    def __init__(self):
        self.not_last_name = ['Ph.D.','APR*','IV','CIPP/US','SPHR®*','Jr.','III']

    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('a.bio_link_img::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])

        if any(name == fullname_list[-1] for name in self.not_last_name) :
            loader.add_value('last_name',fullname_list[-2].replace('*',''))
        else :
            loader.add_value('last_name',fullname_list[-1].replace('*',''))
            
        loader.add_value('firm',self.name)
        loader.add_css('title','div.bio_title::text')
        loader.add_xpath('email','//a[contains(@href,"@michaelbest.com")]/text()')
        educations_list = set([edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul/li')])
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
        loader.add_value('image',response.urljoin(response.css('img.bio_img::attr(src)').get()))
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.michaelbest.com/Our-Firm')
        loader.add_css('office','a.bio_office_link::text')
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