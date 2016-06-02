import os
from os import sys, path
import yaml
from woocommerce import API as WCAPI
from pprint import pprint

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.utils import SanitationUtils
from src.api_clients import WcClient, XeroClient

dir_module = os.path.dirname(sys.argv[0])
if dir_module:
    os.chdir(dir_module)

dir_conf = 'conf'
path_conf_wc = os.path.join(dir_conf, 'wc_api.yaml')
with open(path_conf_wc) as file_conf_wc:
    conf_wc = yaml.load(file_conf_wc)
    for key in ['consumer_key', 'consumer_secret', 'url']:
        assert key in conf_wc, key

path_conf_xero = os.path.join(dir_conf, 'xero_api.yaml')
with open(path_conf_xero) as file_conf_xero:
    conf_xero = yaml.load(file_conf_xero)
    for key in ['consumer_key', 'consumer_secret', 'key_file']:
        assert key in conf_xero, key


wcClient = WcClient(
    **conf_wc
)

xeroClient = XeroClient(
    **conf_xero
)

print len(wcClient.get("products").json()['products'])

print len(xeroClient.items.all())

#
# r = wcapi.get("products?filter[meta]=true&fields=id")
#
# links_str = r.headers.get('link')
#
# for link_str in links_str.split(', '):
#     print repr(link_str)
# response_json = r.json()
#
# if 'products' in response_json:
#     for product in response_json['products']:
#         meta = product.get('product_meta')
#         print meta
#         print product.get('id'), product.get('managing_stock'), product.get('stock_quantity'), product.get('in_stock'), meta.get('MYOB SKU') if meta else None
