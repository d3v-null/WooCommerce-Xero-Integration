import os
from os import sys, path
import yaml
from woocommerce import API as WCAPI
from pprint import pprint

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.utils import SanitationUtils, DebugUtils
from src.api_clients import WcClient, XeroClient

dir_module = os.path.dirname(sys.argv[0])
if dir_module:
    os.chdir(dir_module)


download_wc = True
download_xero = True

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

if download_wc:
    wc_products = wcClient.get_products({
        'core_fields': ['id', 'managing_stock', 'stock_quantity', 'in_stock', 'sku',
                        'status', 'title'],
        'meta_fields': ['MYOB SKU'],
        'filter_params': {
            'search':'Apron'
        },
        'per_page': 100
    })
else:
    wc_products = [{'sku':'a'}]

print "wc products:", len(wc_products)
# pprint(wc_products)

if download_xero:
    xero_products = xeroClient.get_products()
else:
    xero_products = [{'Code':'a'}]

print "xero_products:", len(xero_products)


#group xero products by sku
xero_sku_groups = {}
for xero_product in xero_products:
    xero_sku = xero_product.get('Code')
    if xero_sku:
        xero_sku_groups[xero_sku] = filter(
            None,
            xero_sku_groups.get(xero_sku, []) + [xero_product]
        )

#group wc products by sku
wc_sku_groups = {}
for wc_product in wc_products:
    wc_sku = wc_product.get('meta.MYOB SKU')
    if not wc_sku:
        wc_sku = wc_product.get('sku')
    if wc_sku:
        wc_sku_groups[wc_sku] = filter(
            None,
            wc_sku_groups.get(wc_sku, []) + [wc_product]
        )

#match products on sku
matches = []

for sku, wc_product_group in wc_sku_groups.items():
    if xero_sku_groups.get(sku):
        matches.append((wc_product_group, xero_sku_groups[sku]))

good_matches = []
bad_matches = []
delta_matches = []

for match in matches:
    if len(match[0]) != 1 or len(match[1]) != 1:
        bad_matches.append(match)
        print "bad match:", match
        DebugUtils.register_message(
            ' '.join((SanitationUtils.coerce_unicode(x) for x in \
            ["not 1:1 match", match[0], match[1]]))
        )
        continue
    wc_product = match[0][0]
    xero_product = match[0][0]
    try:
        wc_stock = int(wc_product.get('stock_quantity'))
        xero_stock = int(xero_product.get('QuantityOnHand'))
    except TypeError:
        bad_matches.append(match)
        DebugUtils.register_message(
            ' '.join((SanitationUtils.coerce_unicode(x) for x in \
            ["cant cast to int", repr(wc_product.get('stock_quantity')), \
                                      repr(xero_product.get('QuantityOnHand'))]))
        )
        continue
    if wc_stock == xero_stock:
        good_matches.append(match)
        continue
    else:
        delta_matches.append(match)
        print "delta match:", match
        wc_name = wc_product.get('title')
        xero_name = xero_product.get('Name')
        DebugUtils.register_message(
            ' '.join((SanitationUtils.coerce_unicode(x) for x in \
            ["changing", wc_name, xero_name, wc_stock, xero_stock]))
        )

print "good", len(good_matches)
print "bad", len(bad_matches)
print "delta", len(delta_matches)
