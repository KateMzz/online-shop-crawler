import scrapy
from requests.models import Response
import json
import requests
import math
from scrapy.shell import inspect_response
from scrapy.http import headers, request
from scrapy.crawler import CrawlerProcess
from io import StringIO
from html.parser import HTMLParser



class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def html_to_text(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class AdorebeautySpider(scrapy.Spider):
    name = 'adorebeauty'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'sec-ch-ua': ' Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'x-forwarded-proto': 'https'
        
    }

    def start_requests(self):  
        yield scrapy.Request(url='https://www.adorebeauty.com.au/api/cat?identifier=skin-care&locale=en-AU', callback=self.times_loop, headers=self.headers)

    def times_loop(self, response):
        resp = json.loads(response.body)
        prod_number = int(resp.get('result_count'))
        pages = math.ceil(prod_number/23) 
        for page in range(pages):
            yield scrapy.Request(
                url=f'https://www.adorebeauty.com.au/api/cat?identifier=skin-care&p={page}&locale=en-AU',
                 callback=self.parse_prod_end,
                  headers=self.headers)
   


    def parse_prod_end(self, response):
        resp = json.loads(response.body)
        items = resp.get('products')
        endpoint_bank = []
        for item in items:
            prod_endpoint = item.get('url_key_s')
            if prod_endpoint not in endpoint_bank:
                endpoint_bank.append(prod_endpoint)
                prod_api = f'https://www.adorebeauty.com.au/api/product?identifier={prod_endpoint}&locale=en-AU'
                yield scrapy.Request(url=prod_api, callback=self.parse_prod_info, headers=self.headers)
            else:
                continue

    def parse_prod_info(self, response):
        resp = json.loads(response.body)
        prod_name = resp.get('name_t')
        brand_name = resp.get('manufacturer_t_mv')
        prod_category = resp.get('category_name_t_mv')[0]
        prod_subcategory = resp.get('ec_category_nonindex')
        prod_description = resp.get('short_description_nonindex')
        prod_description = prod_description.replace(';', '')
        prod_description = html_to_text(prod_description)
        prod_description_en = prod_description.encode("ascii", "ignore")
        prod_description_de = prod_description_en.decode()
        prod_benefits = resp.get('description')
        prod_benefits = prod_benefits.replace(';', '')
        prod_benefits = html_to_text(prod_benefits)
        prod_benefits_en = prod_benefits.encode("ascii", "ignore")
        prod_benefits_de = prod_benefits_en.decode()
        awards = ""
        prod_ingredients = resp.get('ingredients')
        # prod_ingredients = html_to_text(prod_ingredients)
        # prod_ingredients_en = prod_ingredients.encode("ascii", "ignore")
        # prod_ingredients_de = prod_ingredients_en.decode()       
        made_without = resp.get('choices_t_mv')       
        price = resp.get('price')
        special_price = resp.get('specialPrice')
        pair_with = ''
        in_stock = resp.get('inStock')
        if in_stock:
            in_stock = 'YES'
        review_img = ''   
        review_ethnicity = ''
        review_age = ''
        review_country = ''
        prod_img = resp.get('productImages')
        reviews = resp.get('reviews')
        reviews_list = []   
        for review in reviews:
            full_review = review.get('review_detail')
            full_review = html_to_text(full_review)
            full_review_en = full_review.encode("ascii", "ignore")
            full_review_de = full_review_en.decode()
            review_dic={
                'review_name' : review.get('review_nickname'),
                'review_stars' : review.get('rating_value'),
                'date_review' : review.get('created_at'),
                'review_title ': review.get('review_title'),
                'review': full_review_de,
                'verified_purchaser' : review.get('verified_purchaser')

            }
            reviews_list.append(review_dic)


        yield{
            
            'prod_name': prod_name,
            'brand_name': brand_name,
            'prod_category': prod_category,
            'prod_subcategory': prod_subcategory,
            'prod_description': prod_description_de,
            'prod_benefits': prod_benefits_de,
            'awards': awards,
            'prod_ingredients': prod_ingredients,
            'made_without': made_without,
            'price': price,
            'special_price': special_price,
            'pair_with': pair_with,
            'in_stock': in_stock,
            'reviewTotal': resp.get('reviewTotal'),
            'reviews': reviews_list,
            'review_img': review_img,
            'review_ethnicity': review_ethnicity,
            'review_age': review_age,
            'review_country': review_country,
            'prod_img': prod_img

    }


# process = CrawlerProcess()
# process.crawl(AdorebeautySpider)
# process.start()
     
        


  