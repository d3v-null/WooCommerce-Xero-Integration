# import os
# import json

# from pprint import pprint
from os import sys, path
from collections import OrderedDict

import wordpress
from wordpress import API as WPAPI
from wordpress.helpers import UrlUtils

from woocommerce import API as WCAPI
from xero import Xero
from xero.auth import PrivateCredentials

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.utils import ValidationUtils, SanitationUtils, DebugUtils

class ApiMixin(object):
    """Abstract helper class for child API client classes"""
    def validate_kwargs(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.kwarg_validations:
                for validation in self.kwarg_validations[key]:
                    error = validation(value)
                    if error:
                        message = "Invalid argument [{key}] = {value}. {error}".format(**locals())
                        DebugUtils.register_error(message)

    def get_products(self, fields=None):
        raise NotImplementedError("get_products not implemented")


class WpClient(ApiMixin):
    """Wraps around the wordpress API and provides extra useful methods"""
    kwarg_validations = {
        'consumer_key':[ValidationUtils.not_none],
        'consumer_secret':[ValidationUtils.not_none],
        'url':[ValidationUtils.is_url],
        # 'wp_user':[ValidationUtils.not_none],
        # 'wp_pass':[ValidationUtils.not_none],
        # 'callback':[ValidationUtils.not_none],
    }

    page_nesting = True

    def __init__(self, *args, **kwargs):
        self.validate_kwargs(**kwargs)
        api_args = {
            'version':'v3',
            'api':'wc-api',
            'basic_auth': True,
            # 'query_string_auth': False,
            'query_string_auth': True,
        }
        for key in [
            'consumer_key', 'consumer_secret', 'url', 'version', 'api',
            'basic_auth', 'query_string_auth'
        ]:
            if key in kwargs:
                api_args[key] = kwargs.get(key)
        self.api = WPAPI(**api_args)


    class WpApiPageIterator(WPAPI):
        """Creates an iterator based on a paginated wc api call"""
        def __init__(self, api, endpoint):
            self.api = api
            self.last_response = self.api.get(endpoint)

        def __iter__(self):
            return self

        def next(self):
            if int(self.last_response.status_code) not in [200]:
                raise UserWarning("request failed with %s: %s -> %s" % (
                    self.last_response.status_code,
                    repr(self.last_response.request.url),
                    repr(self.last_response.content)
                ))
            last_response_json = self.last_response.json()
            last_response_headers = self.last_response.headers
            # print "headers", last_response_headers
            links_str = last_response_headers.get('link', '')
            for link in SanitationUtils.findall_wc_links(links_str):
                if link.get('rel') == 'next' and link.get('url'):
                    self.last_response = self.api.get(link['url'])
                    return last_response_json
            raise StopIteration()

    def get_products(self, params=None):
        if params is None:
            params = {}
        request_params = OrderedDict()
        for key in ['per_page', 'search', 'slug', 'sku']:
            if params.get(key):
                request_params[key] = SanitationUtils.coerce_ascii(params[key])

        endpoint = 'products'
        if params.get('id'):
            _id = params['id']
            assert isinstance(_id, int), "id must be an int"
            endpoint += '/%d' % _id
        if request_params:
            endpoint += '?' + '&'.join([
                key + '=' + val for key, val in request_params.items()
            ])

        print "endpoint is", endpoint

        products = []

        if params.get('id'):
            response = self.api.get(endpoint)
            product = response.json().get('product')
            products.append(product)
            return products

        for page in self.WpApiPageIterator(self.api, endpoint):
            # print "page:", page
            if page.get('products'):
                for page_product in page.get('products'):
                    # print "page_product: ", page_product
                    product = {}
                    for field in params.get('core_fields', []):
                        if field in page_product:
                            product[field] = page_product[field]
                    if page_product.get('product_meta'):
                        page_product_meta = page_product['product_meta']
                        for meta_field in params.get('meta_fields', []):
                            if page_product_meta.get(meta_field):
                                product['meta.'+meta_field] = page_product_meta[meta_field]
                    products.append(product)
        return products

    def update_product(self, _id, data):
        assert isinstance(_id, int), "id must be int"
        assert isinstance(data, dict), "data must be dict"
        return self.api.put("products/%d" % _id, data).json()

class WcClient(WCAPI, ApiMixin):
    """Wraps around the WooCommerce API and provides extra useful methods"""

    kwarg_validations = {
        'consumer_key':[ValidationUtils.not_none],
        'consumer_secret':[ValidationUtils.not_none],
        'url':[ValidationUtils.is_url],
    }

    default_fields = {
        'core_fields': ['id']
    }

    def __init__(self, *args, **kwargs):
        self.validate_kwargs(**kwargs)
        super(WcClient, self).__init__(*args, **kwargs)

    class WcApiPageIterator(object):
        """Creates an iterator based on a paginated wc api call"""
        def __init__(self, api, endpoint):
            self.api = api
            self.last_response = self.api.get(endpoint)

        def __get_endpoint(self, url):
            api_url = self.api._API__get_url('')
            if url.startswith(api_url):
                return url.replace(api_url, '')

        def __iter__(self):
            return self

        def next(self):
            assert self.last_response.status_code not in [404]
            last_response_json = self.last_response.json()
            print "last_response:", self.last_response, self.last_response.text
            if int(self.last_response.status_code) not in [200]:
                raise UserWarning("request failed with %s: %s" % (
                    self.last_response.status_code,
                    self.last_response.text
                ))
            last_response_headers = self.last_response.headers
            links_str = last_response_headers.get('link', '')
            for link in SanitationUtils.findall_wc_links(links_str):
                if link.get('rel') == 'next' and link.get('url'):
                    self.last_response = self.api.get(
                        self.api.__get_endpoint(link['url'])
                    )
                    return last_response_json
            raise StopIteration()

    def get_products(self, params=None):
        if params is None:
            params = self.default_fields
        request_params = OrderedDict()
        incl_fields = params.get('core_fields', [])
        extra_fields = []
        if params.get('meta_fields'):
            request_params['filter[meta]'] = 'true'
            extra_fields.append('product_meta')
        if params.get('core_fields'):
            request_params['fields'] = ','.join(incl_fields + extra_fields)
        if params.get('filter_params'):
            for key, val in params['filter_params'].items():
                request_params['filter[%s]' % key] = val
        for key in ['per_page', 'search', 'slug', 'sku']:
            if params.get(key):
                request_params[key] = SanitationUtils.coerce_ascii(params[key])

        endpoint = 'products'
        if params.get('id'):
            _id = params['id']
            assert isinstance(_id, int), "id must be an int"
            endpoint += '/%d' % _id
        if request_params:
            endpoint += '?' + '&'.join([
                key + '=' + val for key, val in request_params.items()
            ])

        # print self._API__get_url(endpoint)
        # print endpoint

        products = []

        if params.get('id'):
            response = self.get(endpoint)
            product = response.json().get('product')
            products.append(product)
            return products

        for page in self.WcApiPageIterator(self, endpoint):
            if page.get('products'):
                for page_product in page.get('products'):
                    product = {}
                    for field in params.get('core_fields', []):
                        if field in page_product:
                            product[field] = page_product[field]
                    if page_product.get('product_meta'):
                        page_product_meta = page_product['product_meta']
                        for meta_field in params.get('meta_fields', []):
                            if page_product_meta.get(meta_field):
                                product['meta.'+meta_field] = page_product_meta[meta_field]
                    products.append(product)
            elif params.get('id'):
                print page
                products.append(page)
                break
        return products

    def update_product(self, _id, data):
        assert isinstance(_id, int), "id must be int"
        assert isinstance(data, dict), "data must be dict"
        return self.put("products/%d" % _id, data).json()

class XeroClient(Xero, ApiMixin):
    """Wraps around the Xero API and provides extra useful methods"""
    kwarg_validations = {
        'consumer_key':[ValidationUtils.not_none],
        'consumer_secret':[ValidationUtils.not_none],
        'key_file':[ValidationUtils.not_none, ValidationUtils.is_file],
    }

    def __init__(self, **kwargs):
        self.validate_kwargs(**kwargs)
        with open(kwargs.get('key_file')) as file_key:
            rsa_key = file_key.read()

        credentials = PrivateCredentials(kwargs.get('consumer_key'), rsa_key)
        super(self.__class__, self).__init__(credentials)

    def get_products(self, fields=None):
        return self.items.all()
