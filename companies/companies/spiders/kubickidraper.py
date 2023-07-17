import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'kubickidraper'
    allowed_domains = ['kubickidraper.com']
    start_urls = ['https://www.kubickidraper.com/?t=47&format=xml&directive=0&stylesheet=atty_json']


    def __init__(self):
        self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]


    def parse(self, response):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            try:
                for item in response.json()['attys'][ch.upper()]:
                    loader = ItemLoader(CompaniesItem(),response)
                    loader.add_value('url','')
                    fullname_list = item['N'].split()
                    if any(name == fullname_list[0] for name in self.not_names):
                        loader.add_value('first_name', fullname_list[1])
                    else :
                        loader.add_value('first_name', fullname_list[0])
                    if any(name == fullname_list[-1] for name in self.not_names):
                        loader.add_value('last_name', fullname_list[-2])
                    else :
                        loader.add_value('last_name', fullname_list[-1])
                    loader.add_value('firm',self.name)
                    loader.add_value('title',item['R'])
                    loader.add_value('email',item['E'])
                    # educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('')]
                    # try :
                    #     law_school , year = self.get_law_school(educations_list)
                    #     loader.add_value('law_school',law_school)
                    #     loader.add_value('law_school_graduation_year',year)
                    # except TypeError : 
                    #     pass 
                    # try : 
                    #     undergraduate_school, year = self.get_undergraduate_school(educations_list)
                    #     loader.add_value('undergraduate_school',undergraduate_school)
                    #     loader.add_value('undergraduate_school_graduation_year',year)
                    # except TypeError :
                    #     pass
                    loader.add_value('image',item['V'])
                    loader.add_value('bio',item['DESCRIPTION'][3:-5])
                    loader.add_value('firm_bio','https://www.kubickidraper.com/our-firm')
                    loader.add_value('office','')
                    yield loader.load_item()
            except KeyError:
                continue



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


                