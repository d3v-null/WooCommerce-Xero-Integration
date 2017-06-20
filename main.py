import os
from os import sys, path
import csv
from copy import copy
from collections import OrderedDict
from time import sleep
# from woocommerce import API as WCAPI
from pprint import pprint
from requests.exceptions import ReadTimeout

import yaml
from tabulate import tabulate
import argparse

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.utils import SanitationUtils, DebugUtils, ProgressCounter
from src.api_clients import WcClient, XeroClient, WpClient
from src.containers import XeroProduct, WCProduct, WCAPIProduct, WCCSVProduct

def main():
    dir_module = os.path.dirname(sys.argv[0])
    if dir_module:
        os.chdir(dir_module)

    #default arguments
    xero_config_file = 'xero_api.yaml'
    wc_config_file = 'wc_api_test.yaml'
    xero_report_file = 'xero_products.csv'
    wc_report_file = 'wc_products.csv'
    new_wc_report_file = 'new_wc_products.csv'

    parser = argparse.ArgumentParser(description='Merge products between Xero and WC')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbosity", action="count", default=2,
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
    parser.add_argument('--wc-import-file',
                        help='location of wc import file, used if can\'t download products')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update-wc', help='update the wc database',
                       action="store_true", default=None)
    group.add_argument('--report-wc-and-quit', help='report wc data and quit',
                       action="store_true", default=None)
    group.add_argument('--report-xero-and-quit', help='report wc data and quit',
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
        if args.xero_config_file is not None:
            xero_config_file = args.xero_config_file
        if args.wc_config_file is not None:
            wc_config_file = args.wc_config_file

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

    wc_client = WpClient(
        **conf_wc
    )

    xero_client = XeroClient(
        **conf_xero
    )

    # fill wc_products

    wc_products = []
    wc_container_class = WCAPIProduct
    if args.download_wc:
        wc_products_data = wc_client.get_products({
            'core_fields': [
                wc_container_class.id_key,
                wc_container_class.managing_stock_key,
                wc_container_class.stock_level_key,
                wc_container_class.stock_status_key,
                wc_container_class.second_sku_key,
                wc_container_class.title_key,
                # 'status',
            ],
            'meta_fields': ['MYOB SKU'],
            'per_page': conf_wc.get('per_page', 300)
        })
        wc_products = [wc_container_class(data) for data in wc_products_data]

        if wc_products:
            print "products downloaded from WC"
        else:
            print "it looks like there was a problem downloading products from the website."
            print "you can export the products from the website manually, and try again."
            quit()

    elif args.wc_import_file:
        wc_container_class = WCCSVProduct
        with open(args.wc_import_file, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                wc_products.append(wc_container_class(row))

    if wc_products:
        DebugUtils.register_message("reporting WC")

        with open(wc_report_file, 'w+') as report_file:
            csv_writer = csv.writer(report_file)
            csv_writer.writerow(wc_container_class.report_attrs)
            for wc_product in wc_products:
                csv_writer.writerow([
                    SanitationUtils.coerce_ascii(getattr(wc_product, attr)) \
                    for attr in wc_container_class.report_attrs
                ])

        for wc_product in wc_products:
            wc_sku = wc_product.get(wc_container_class.sku_key)
            wc_second_sku = wc_product.get(wc_container_class.second_sku_key)
            wc_managing_stock = wc_product.get(wc_container_class.managing_stock_key)
            wc_stock_level = wc_product.get(wc_container_class.stock_level_key)
            if not wc_managing_stock and wc_stock_level < 5:
                DebugUtils.register_warning('not tracked: %s' % wc_sku)
            if wc_sku and wc_sku != wc_second_sku:
                DebugUtils.register_warning('primary SKU (%s) != secondary SKU (%s) ' % (wc_sku, wc_second_sku))

    if args.report_wc_and_quit:
        quit()

    if args.download_xero:
        xero_products_data = xero_client.get_products()
        xero_products = [XeroProduct(data) for data in xero_products_data]
        if xero_products:
            print "products downloaded from Xero"
        else:
            print "it looks like there was a problem downloading products from Xero."
            print "check your config and try again."
            quit()


    else:
        xero_products_data = [
            {'Code':'a', 'Name':'A', 'QuantityOnHand':2.0, 'IsTrackedAsInventory':True},
            {'Code':'c', 'QuantityOnHand':0.0, 'IsTrackedAsInventory':True}
        ]
        xero_products = [XeroProduct(data) for data in xero_products_data]


    if xero_products:
        DebugUtils.register_message("reporting Xero")

        with open(xero_report_file, 'w+') as report_file:
            csv_writer = csv.writer(report_file)
            csv_writer.writerow(XeroProduct.report_attrs)
            for xero_product in xero_products:
                csv_writer.writerow([
                    SanitationUtils.coerce_ascii(getattr(xero_product, attr)) \
                    for attr in XeroProduct.report_attrs
                ])

    if args.report_xero_and_quit:
        quit()

    DebugUtils.register_message("xero_products: %s" % (len(xero_products)))

    #group xero products by sku
    xero_sku_groups = {}
    for xero_product in xero_products:
        xero_name = xero_product.title
        xero_sku = xero_product.sku
        xero_stock = xero_product.stock_level
        xero_id = xero_product.pid
        # xero_managing_stock = xero_product.managing_stock

        DebugUtils.register_message(" ".join(
            SanitationUtils.coerce_ascii(x) for x in \
            ["processing xero", xero_id, xero_name, xero_sku, xero_stock]
        ))

        if xero_sku:
            xero_sku_groups[xero_sku] = [
                prod for prod in \
                xero_sku_groups.get(xero_sku, []) + [xero_product] \
                if prod
            ]

    #group wc products by sku
    wc_sku_groups = {}
    for wc_product in wc_products:
        wc_name = wc_product.title
        wc_sku = wc_product.sku
        wc_stock = wc_product.stock_level
        wc_id = wc_product.pid
        DebugUtils.register_message(" ".join(
            SanitationUtils.coerce_ascii(x) for x in \
            ["processing wc", wc_id, wc_name, wc_sku, wc_stock]
        ))
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
    # skip_matches = []
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
        # wc_name = wc_product.title
        # xero_name = xero_product.title
        wc_level = wc_product.stock_level
        xero_level = xero_product.stock_level
        delta_row = [
            SanitationUtils.coerce_ascii(cell) for cell in\
            [
                wc_product, wc_level, wc_product.managing_stock,
                xero_product, xero_level, xero_product.managing_stock,
                "%+3d" % (xero_level - wc_level)
            ]
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

    DebugUtils.register_message("good:  %3d" % len(good_matches))
    DebugUtils.register_message("bad:   %3d" % len(bad_matches))
    DebugUtils.register_message("delta: %3d" % len(delta_matches))

    # report bad

    if bad_data:
        DebugUtils.register_message("CONFLICTS:\n%s" % tabulate(
            bad_data,
            headers=('WC Products', 'Xero Products')
        ))

    # report deltas

    if delta_matches:
        DebugUtils.register_message("CHANGES:\n%s" % tabulate(
            delta_data, headers=(
                'WC Product', 'stock', 'managing',
                'Xero Product', 'stock', 'managing', 'delta'
            )
        ))

    if new_wc_products:
        DebugUtils.register_message("reporting WC to %s" % new_wc_report_file)

        with open(new_wc_report_file, 'w+') as report_file:
            csv_writer = csv.writer(report_file)
            csv_writer.writerow(WCProduct.report_attrs)
            for wc_product in new_wc_products:
                csv_writer.writerow([
                    SanitationUtils.coerce_ascii(getattr(wc_product, attr)) \
                    for attr in WCProduct.report_attrs
                ])

    if args.update_wc:
        if new_wc_products:
            update_progress_counter = ProgressCounter(len(new_wc_products))
            DebugUtils.register_message("Updating WC")

            for count, product in enumerate(new_wc_products):
                update_progress_counter.maybe_print_update(count)
                data = {"product": OrderedDict([
                    (WCAPIProduct.stock_level_key, product.stock_level),
                    (WCAPIProduct.stock_status_key, product.stock_status),
                    (WCAPIProduct.managing_stock_key, product.managing_stock)
                ])}

                response = None
                try:
                    response = wc_client.update_product(product.pid, data)
                except ReadTimeout as e:
                    DebugUtils.register_warning(
                        "request timed out, trying again after a short break"
                    )
                    sleep(10)
                    try:
                        response = wc_client.update_product(product.pid, data)
                    except ReadTimeout as e:
                        DebugUtils.register_error(
                            ("!!! API keeps timing out, "
                             "please try again later or manually upload the CSV file")
                        )
                        quit()
                finally:
                    DebugUtils.register_message("API responeded :%s" % response)
        else:
            print "no updates need to be made"

    print "Sync complete."

if __name__ == '__main__':
    main()
