import os
import sys
import yaml
import json
from woocommerce import API as WCAPI
from pprint import pprint

dir_parent = os.path.dirname(os.path.dirname(sys.argv[0]))
if dir_parent:
    os.chdir(dir_parent)
dir_conf = 'conf'
path_conf_wc = os.path.join(dir_conf, 'wc_api.yaml')
with open(path_conf_wc) as file_conf_wc:
    conf_wc = yaml.load(file_conf_wc)
    for key in ['consumer_key', 'consumer_secret', 'url']:
        assert key in conf_wc, key

wcapi = WCAPI(
    **conf_wc
)

r = wcapi.get("products?filter[meta]=true")

links_str = r.headers.get('link')

for link_str in links_str.split(', '):
    print repr(link_str)
response_json = r.json()

if 'products' in response_json:
    for product in response_json['products']:
        print product.get('id'), product.get('managing_stock'), product.get('stock_quantity'), product.get('in_stock'), product.get('product_meta', {}).get('MYOB SKU')
