import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class WilliamsmullenSpider(scrapy.Spider):
    name = 'williamsmullen'
    allowed_domains = ['williamsmullen.com']
    start_urls = ['http://williamsmullen.com/']

    def __init__(self):
        self.listing_template = 'https://www.williamsmullen.com/people?page={}'
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.']


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        people_urls = [response.urljoin(url) for url in response.xpath('//span//a[contains(@href,"people")]/@href').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1.title::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.position-title::text')
        loader.add_value('email',response.xpath('//dd//a[contains(@href,"mailto:")]/@href').get().replace('mailto:',''))
        educations_list = [edu.get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul/li/text()[1]')]
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
        loader.add_css('image','div#page-header::attr(style)',re='url\(([\s\S]+)\)')
        loader.add_xpath('bio','string(//div[@id="main-bio"])')
        loader.add_value('firm_bio','https://www.williamsmullen.com/story')
        loader.add_css('office','a.office::text')
        yield loader.load_item()


    def get_total_pages(self,response):
        return max([int(number) for number in response.css('li.pager-current').re('\d+')])


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