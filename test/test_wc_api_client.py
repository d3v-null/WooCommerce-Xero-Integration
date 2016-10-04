# coding=utf-8

from os import sys, path
import os
import yaml
from unittest import TestCase, main, skip
import unittest
import re

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from src.api_clients import *
from src.containers import API_Product, WC_API_Product

class TestProductClient(TestCase):
    def setUp(self):
        dir_parent = os.path.dirname(os.path.dirname(sys.argv[0]))
        if dir_parent:
            os.chdir(dir_parent)
        dir_conf = 'conf'
        path_conf_wc = os.path.join(dir_conf, 'wc_api_test_local.yaml')
        with open(path_conf_wc) as file_conf_wc:
            conf_wc = yaml.load(file_conf_wc)
            for key in ['consumer_key', 'consumer_secret', 'url']:
                assert key in conf_wc, key

        self.client = WcClient(**conf_wc)

    def test_get_product(self):
        wc_products = self.client.get_products({
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
            # 'filter_params': {
            #     'search':'Apron'
            # },
            # 'search':'Apron',
            'id':10481,
            # 'sku':'BOBB#MC',
            'per_page': 300
        })
        self.assertEqual(len(wc_products), 1)
        product = WC_API_Product( wc_products[0])
        self.assertEqual(product.sku, "PM#07")

    def test_update_product(self):
        data = {
            "product":{
                "regular_price": "24.54"
            }
        }
        print self.client.update_product(10481, data)

if __name__ == '__main__':
    main()
    # testSuite = unittest.TestSuite()
    # testSuite.addTest(TestProductClient('test_update_product'))
    # unittest.TextTestRunner().run(testSuite)
