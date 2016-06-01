import os
import json

from pprint import pprint
from os import sys, path

from woocommerce import API as WCAPI
from xero import Xero
from xero.auth import PrivateCredentials

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from src.utils import ValidationUtils, SanitationUtils, DebugUtils

class ApiMixin(object):
    """Doctsring for API Mixin"""
    def validateKwargs(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.kwargValidations:
                for validation in self.kwargValidations[key]:
                    error = validation(value)
                    if error:
                        message = "Invalid argument [{key}] = {value}. {error}".format(**locals())
                        DebugUtils.registerError(message)


class WcClient(WCAPI, ApiMixin):
    kwargValidations = {
        'consumer_key':[ValidationUtils.isNotNone],
        'consumer_secret':[ValidationUtils.isNotNone],
        'url':[ValidationUtils.isUrl],
    }

class XeroClient(Xero, ApiMixin):
    kwargValidations = {
        'consumer_key':[ValidationUtils.isNotNone],
        'consumer_secret':[ValidationUtils.isNotNone],
        'key_file':[ValidationUtils.isNotNone, ValidationUtils.isFile],
    }

    def __init__(self, **kwargs):
        self.validateKwargs(**kwargs)
        with open(kwargs.get('key_file')) as file_key:
            rsa_key = file_key.read()

        credentials = PrivateCredentials(kwargs.get('consumer_key'), rsa_key)
        super(self.__class__, self).__init__(credentials)
