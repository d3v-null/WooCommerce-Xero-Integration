import os
from os import sys, path
import yaml
from copy import copy
from collections import OrderedDict
# from woocommerce import API as WCAPI
from pprint import pprint
from tabulate import tabulate
import argparse

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.utils import SanitationUtils, DebugUtils
from src.api_clients import WcClient, XeroClient
from src.containers import Xero_API_Product, WC_API_Product

def main():
    dir_module = os.path.dirname(sys.argv[0])
    if dir_module:
        os.chdir(dir_module)

    #default arguments

    download_wc = False
    download_xero = False
    download_wc = True
    download_xero = True
    update_wc = False
    update_wc = True
    xero_config_file = 'xero_api.yaml'
    wc_config_file = 'wc_api_test.yaml'
    report_and_quit = False

    parser = argparse.ArgumentParser(description = 'Merge products between Xero and WC')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbosity", action="count",
                        help="increase output verbosity")
    group.add_argument("-q", "--quiet", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--download-xero', help='download the xero data',
                       action="store_true", default=None)
    group.add_argument('--skip-download-xero', help='use the local xero file instead\
        of downloading the xero data', action="store_false", dest='download_xero')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--download-wc', help='download the wc data',
                       action="store_true", default=None)
    group.add_argument('--skip-download-wc', help='use the local wc file instead\
        of downloading the wc data', action="store_false", dest='download_wc')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update-wc', help='update the wc database',
                       action="store_true", default=None)
    group.add_argument('--report-and-quit', help='report wc data and quit',
                       action="store_true", default=None)
    group.add_argument('--skip-update-wc', help='don\'t update the wc database',
                       action="store_false", dest='update_wc')
    parser.add_argument('--xero-config-file', help='location of xero config file')
    parser.add_argument('--wc-config-file', help='location of wc config file')
    args = parser.parse_args()

    if args:
        if args.verbosity > 0:
            DebugUtils.CURRENT_VERBOSITY = args.verbosity
        elif args.quiet:
            DebugUtils.CURRENT_VERBOSITY = 0
        if args.download_wc is not None:
            download_wc = args.download_wc
        if args.download_xero is not None:
            download_xero = args.download_xero
        if args.update_wc is not None:
            update_wc = args.update_wc
        if args.xero_config_file is not None:
            xero_config_file = args.xero_config_file
        if args.wc_config_file is not None:
            wc_config_file = args.wc_config_file
        if args.report_and_quit is not None:
            report_and_quit = args.report_and_quit

    dir_conf = 'conf'
    path_conf_wc = os.path.join(dir_conf, wc_config_file)
    with open(path_conf_wc) as file_conf_wc:
        conf_wc = yaml.load(file_conf_wc)
        for key in ['consumer_key', 'consumer_secret', 'url']:
            assert key in conf_wc, key

    path_conf_xero = os.path.join(dir_conf, xero_config_file)
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
            'core_fields': [
                WC_API_Product.id_key,
                WC_API_Product.managing_stock_key,
                WC_API_Product.stock_level_key,
                WC_API_Product.stock_status_key,
                WC_API_Product.second_sku_key,
                WC_API_Product.title_key,
                # 'status',
            ],
            'meta_fields': ['MYOB SKU'],
            'per_page': 300
        })
    else:
        wc_products = [
            {'id': 1, 'meta.MYOB SKU':'a', 'title': 'A', 'stock_quantity': 1, 'managing_stock': True},
            {'id': 2, 'sku':'a', 'title':'B', 'stock_quantity': 2, 'managing_stock': True},
            {'id': 3, 'sku':'c', 'title':'C', 'stock_quantity': 3, 'managing_stock': True}]

    print "wc products:", len(wc_products)
    pprint(wc_products)
    tabulate(wc_products)
    for wc_product in wc_products:
        wc_sku = wc_product.get(WC_API_Product.sku_key)
        wc_second_sku = wc_product.get(WC_API_Product.second_sku_key)
        wc_managing_stock = wc_product.get(WC_API_Product.managing_stock_key)
        wc_stock_level = wc_product.get(WC_API_Product.stock_level_key)
        if not wc_managing_stock and wc_stock_level < 5:
            print 'not tracked:', wc_sku
        if wc_sku != wc_second_sku:
            print 'not the same:', wc_sku, wc_second_sku

    if report_and_quit:
        quit()

    if download_xero:
        xero_products = xeroClient.get_products()
    else:
        xero_products = [
            {'Code':'a', 'Name':'A', 'QuantityOnHand':2.0, 'IsTrackedAsInventory':True},
            {'Code':'c', 'QuantityOnHand':0.0, 'IsTrackedAsInventory':True}
        ]

    DebugUtils.register_message( "xero_products: %s" % (len(xero_products)) )

    #group xero products by sku
    xero_sku_groups = {}
    for xero_product_data in xero_products:
        xero_product = Xero_API_Product(xero_product_data)
        xero_name = xero_product.title
        xero_sku = xero_product.sku
        xero_stock = xero_product.stock_level
        xero_id = xero_product.pid
        xero_managing_stock = xero_product.managing_stock

        DebugUtils.register_message( " ".join(
            SanitationUtils.coerce_ascii(x) for x in \
            [ "processing xero", xero_id, xero_name, xero_sku, xero_stock]
        ) )

        if xero_sku:
            xero_sku_groups[xero_sku] = [
                prod for prod in \
                xero_sku_groups.get(xero_sku, []) + [xero_product] \
                if prod
            ]

    #group wc products by sku
    wc_sku_groups = {}
    for wc_product_data in wc_products:
        wc_product = WC_API_Product(wc_product_data)
        wc_name = wc_product.title
        wc_sku = wc_product.sku
        wc_stock = wc_product.stock_level
        wc_id = wc_product.pid
        DebugUtils.register_message( " ".join(
            SanitationUtils.coerce_ascii(x) for x in \
            ["processing wc", wc_id, wc_name, wc_sku, wc_stock]
        ) )
        if wc_sku:
            wc_sku_groups[wc_sku] = [
                prod for prod in \
                wc_sku_groups.get(wc_sku, []) + [wc_product] \
                if prod
            ]

    #match products on sku
    matches = []

    for sku, wc_product_group in wc_sku_groups.items():
        if xero_sku_groups.get(sku):
            matches.append((wc_product_group, xero_sku_groups[sku]))

    good_matches = []
    bad_matches = []
    skip_matches = []
    bad_data = []
    delta_matches = []
    delta_data = []
    new_wc_products = []
    new_data = []

    for match in matches:
        matched_wc_products = match[0]
        matched_xero_products = match[1]
        if len(matched_wc_products) != 1 or len(matched_xero_products) != 1:
            bad_matches.append(match)
            # print "bad match:", match
            DebugUtils.register_message(
                ' '.join((SanitationUtils.coerce_unicode(x) for x in \
                ["not 1:1 match", matched_wc_products, matched_xero_products]))
            )
            bad_row = [
                "; ".join([
                    SanitationUtils.coerce_ascii(product) for product in products
                ]) for products in [matched_wc_products, matched_xero_products]
            ]
            bad_data.append(bad_row)
            continue
        wc_product = matched_wc_products[0]
        xero_product = matched_xero_products[0]
        if wc_product.managing_stock != xero_product.managing_stock:
            delta_matches.append(match)
            continue
        try:
            for product in wc_product, xero_product:
                assert product.stock_level is not None
            wc_stock = wc_product.stock_level
            xero_stock = xero_product.stock_level
        except (TypeError, ValueError, AssertionError):
            bad_matches.append(match)
            DebugUtils.register_message(
                ' '.join((SanitationUtils.coerce_unicode(x) for x in \
                ["cant cast to int", repr(wc_product.get('stock_quantity')), \
                                     repr(xero_product.get('QuantityOnHand'))]))
            )
            continue
        if wc_stock != xero_stock:
            delta_matches.append(match)
            continue
        good_matches.append(match)

    for delta_match in delta_matches:
        wc_product = delta_match[0][0]
        xero_product = delta_match[1][0]
        wc_name = wc_product.title
        xero_name = xero_product.title
        delta_row = [
            SanitationUtils.coerce_ascii(cell) for cell in\
            [wc_product, wc_product.stock_level, wc_product.managing_stock, \
             xero_product, xero_product.stock_level, xero_product.managing_stock]
        ]
        delta_data.append(delta_row)

        new_wc_product = copy(wc_product)
        new_wc_product.stock_level = xero_product.stock_level
        new_wc_product.managing_stock = xero_product.managing_stock
        new_wc_products.append(new_wc_product)

        new_data.append([
            SanitationUtils.coerce_ascii(x) for x in \
            [new_wc_product, new_wc_product.stock_level,
             new_wc_product.stock_status, new_wc_product.managing_stock]
        ])

        # DebugUtils.register_message(
        #     ' '.join((SanitationUtils.coerce_unicode(x) for x in \
        #     ["changing", wc_name, xero_name, wc_stock, xero_stock]))
        # )

    print "good", len(good_matches)
    print "bad", len(bad_matches)
    print "delta", len(delta_matches)

    # report bad

    print "CONFLICTS:"

    print tabulate(bad_data)

    # report deltas

    print "CHANGES:"

    print tabulate(delta_data)

    print "NEW WORDPRESS RECORDS"

    print tabulate(new_data)

    if update_wc:
        for product in new_wc_products:
            data = {"product": OrderedDict([
                (WC_API_Product.stock_level_key, product.stock_level),
                (WC_API_Product.stock_status_key, product.stock_status),
                (WC_API_Product.managing_stock_key, product.managing_stock)
            ])}

            print wcClient.update_product(product.pid, data)
    else:
        print "not updating"

if __name__ == '__main__':
    main()
