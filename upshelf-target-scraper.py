import re
import json
import requests
from bs4 import BeautifulSoup

session = requests.session()

url = r'https://www.target.com/p/apple-iphone-13-pro-max/-/A-84616123?preselect=84240109#lnk=sametab'
response = session.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'lxml')

api = re.search('"apiKey":"([a-z0-9]+)"', soup.prettify()).group(1)
tcin = re.search(r'A-([0-9]+)?', url).group(1)
print(f'Scraping details of product with tcin: {tcin}')

if re.search(r'preselect=([0-9]+)#', url):
    child = re.search(r'preselect=([0-9]+)#', url).group(1)
else:
    child = None

api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key={api}&tcin={tcin}&store_id=1301&pricing_store_id=1301&has_financing_options=true&has_size_context=true'
response = session.get(api_url)
response.raise_for_status()

output = {}
for x in response.json()['data']['product']['children']:
    if child is None or x['tcin'] == child:
        output['title'] = x['item']['product_description']['title']
        output['retail_price'] = x['connected_commerce']['products'][0]['locations'][0]['carriers'][0]['price']['current_retail']
        output['monthly_price'] = x['connected_commerce']['products'][0]['locations'][0]['carriers'][0]['price']['payment_plan']['installment']
        output['highlights'] = x['item']['product_description']['soft_bullets']['bullets']
        output['specifications'] = {}
        for k in x['item']['product_description']['bullet_descriptions']:
            k = k.replace('<B>', '').replace('</B> ', '')
            output['specifications'].update({k.strip().split(':')[0]: ':'.join(k.strip().split(':')[1:])})
        output['description'] = x['item']['product_description']['downstream_description']
        output['urls'] = [x['item']['enrichment']['images']['primary_image_url']]
        output['urls'].extend(x['item']['enrichment']['images']['alternate_image_urls'])
        break

q_url = f'https://r2d2.target.com/ggc/Q&A/v1/question-answer?type=product&questionedId={tcin}&page=0&size=10&sortBy=MOST_ANSWERS&key={api}&errorTag=drax_domain_questions_api_error'
response = session.get(q_url)
response.raise_for_status()
data = response.json()
output['questions_&_answers'] = {x['text']: [y['text'] for y in x['answers']] for x in data['results']}

with open('product_details.json', 'w') as fp:
    json.dump(output, fp, indent=3)
print(f'Output stored in file: product_details.json')
exit()
