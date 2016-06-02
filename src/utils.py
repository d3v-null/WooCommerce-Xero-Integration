import inspect
# import re
import os
# from os import path, sys

from kitchen.text import converters

class SanitationUtils(object):
    """Provides utiy methods for sanitizing data"""
    regex_url = \
        r"https?:\/\/(?:www\.)?" + \
        r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)"
    regex_wc_link = r"<(?P<url>{0})>; rel=\"(?P<rel>\w+)\"".format(regex_url)

    @staticmethod
    def wrap_full_match(regex):
        """Wraps a given regylar expression so that it encompases a full match"""
        return r"^{}$".format(regex)

    @staticmethod
    def wrap_paren(regex):
        """Wraps a given regylar expression in parens"""
        return r"({})".format(regex)

    @classmethod
    def coerce_unicode(cls, thing):
        """Coerces anything into a unicode object including utf8 bytestring and None"""

        if thing is None:
            unicode_return = u""
        else:
            unicode_return = converters.to_unicode(thing, encoding="utf8")
        assert \
            isinstance(unicode_return, unicode), \
            "something went wrong, should return unicode not %s" % type(unicode_return)
        return unicode_return

    @classmethod
    def findall_wc_link(cls, string):
        """Finds all wc style link occurences in a given string"""
        pass

class ValidationUtils(object):
    """Provides utiy methods for validating data"""

    @staticmethod
    def not_none(value):
        """Returns a warning string if a given value is None"""
        if value is None:
            return "must not be None"

    @staticmethod
    def is_file(value):
        """Returns a warning string if a given value is not a valid file"""
        if not os.path.isfile(value):
            return "must be a file"

    @staticmethod
    def is_url(value):
        """Returns a warning string if a given value does not look like a URL"""
        pass


class DebugUtils(object):
    """Provides utiy methods for debugging the program"""

    ERROR_VERBOSITY = 1
    WARNING_VERBOSITY = 2
    MESSAGE_VERBOSITY = 3

    @staticmethod
    def get_procedure():
        """Gets the name of the procedure calling this method"""
        return inspect.stack()[1][3]

    @staticmethod
    def get_caller_procedure():
        """Gets the name of the procedure calling the procedure calling this method"""
        return inspect.stack()[2][3]

    @classmethod
    def register_message(cls, message, severity=None):
        """Registers a message with any severity and prints if verbose enough"""
        if severity is None:
            severity = cls.MESSAGE_VERBOSITY
        print cls.get_procedure(), message

    @classmethod
    def register_error(cls, message):
        """Registers a message with warning severity and prints if verbose enough"""
        cls.register_message(message, cls.ERROR_VERBOSITY)
