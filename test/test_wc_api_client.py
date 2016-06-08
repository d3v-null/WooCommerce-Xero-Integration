# coding=utf-8

from os import sys, path
import os
import yaml
from unittest import TestCase, main, skip
import re

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from src.api_clients import *

class TestSanitationUtils(TestCase):
    def setUp(self):
        dir_parent = os.path.dirname(os.path.dirname(sys.argv[0]))
        if dir_parent:
            os.chdir(dir_parent)
        dir_conf = 'conf'
        path_conf_wc = os.path.join(dir_conf, 'wc_api.yaml')
        with open(path_conf_wc) as file_conf_wc:
            conf_wc = yaml.load(file_conf_wc)
            for key in ['consumer_key', 'consumer_secret', 'url']:
                assert key in conf_wc, key

        self.client = WcClient(**conf_wc)

    def test_upload_product(self):
        pass


if __name__ == '__main__':
    main()
