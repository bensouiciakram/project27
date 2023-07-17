import traceback 

spider = input('enter the spider : ')
listing_template = input('enter the listing_template : ')
people_urls = input('enter the people_urls : ')
fullname_selector = input('enter the fullname_selector : ')
title_selector = input('enter the title_selector : ')
email_selector = input('enter the email_selector : ')
education_selector = input('enter the education_selector : ')
image = input('enter the image : ')
bio = input('enter the bio : ')
firm_selector = input('enter the firm_selector : ')
office_selector = input('enter the office_selector : ')


with open('template.txt','r') as file : 
    template = file.read()


template = template.format(
        spider=spider,
        listing_template = listing_template,
        people_urls =people_urls ,
        fullname_selector = fullname_selector ,
        title_selector = title_selector,
        email_selector = email_selector ,
        education_selector = education_selector,
        image = image,
        bio =bio,
        firm_selector =firm_selector ,
        office_selector = office_selector
    )

with open('companies/spiders/{}.txt'.format(spider),'w') as file :
    file.write(template)
