# import os
# import json

# from pprint import pprint
from os import sys, path

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


class WcClient(WCAPI, ApiMixin):
    """Doctsring for WcClient"""
    kwarg_validations = {
        'consumer_key':[ValidationUtils.not_none],
        'consumer_secret':[ValidationUtils.not_none],
        'url':[ValidationUtils.is_url],
    }

    default_fields = {
        'core_fields': ['id']
    }

    class WcApiCallIterator(WCAPI):
        """Creates an iterator based on a paginated wc api call"""
        def __init__(self, call_params):
            r = self.get(**call_params)
            self.last_response_json = r.json()
            self.last_header_json = r.headers    


    def get_products(self, fields=None):
        if fields is None:
            fields = self.default_fields

        # get first list of products,

class XeroClient(Xero, ApiMixin):
    """Doctsring for XeroClient"""
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
        pass
