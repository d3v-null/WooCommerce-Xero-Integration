import inspect
import re
import os
# from os import path, sys
import time

from kitchen.text import converters

class SanitationUtils(object):
    """Provides utiy methods for sanitizing data"""
    # url regex by http://daringfireball.net/2010/07/improved_regex_for_matching_urls
    regex_url = \
        ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)'+\
        ur'(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+'+\
        ur'(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?]))'
    regex_wc_link = ur"<(?P<url>{0})>; rel=\"(?P<rel>\w+)\"".format(regex_url)

    @staticmethod
    def maybe_wrap_full_match(regex):
        """Wraps a given regylar expression so that it encompases a full match"""
        if regex[0] == '^' and regex[-1] == '$':
            return regex
        else:
            return r"^{}$".format(regex)

    @staticmethod
    def maybe_wrap_paren(regex):
        """Wraps a given regular expression in parens if necessary"""
        if regex[0] == '(' and regex[-1] == ')':
            return regex
        else:
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
    def coerce_bytestr(cls, thing):
        unicode_thing = cls.coerce_unicode(thing)
        byte_return = converters.to_bytes(unicode_thing, "utf8")
        assert \
            isinstance(byte_return, str), \
            "something went wrong, should return str not %s" % type(byte_return)
        return byte_return

    @classmethod
    def coerce_ascii(cls, thing):
        unicode_thing = cls.coerce_unicode(thing)
        ascii_return = converters.to_bytes(unicode_thing, "ascii", "backslashreplace")
        assert \
            isinstance(ascii_return, str), \
            "something went wrong, should return str not %s" % type(ascii_return)
        return ascii_return

    @classmethod
    def sanitize_container_value(cls, thing):
        if isinstance(thing, str):
            thing = SanitationUtils.coerce_unicode(thing)
        return thing

    @classmethod
    def findall_wc_links(cls, string):
        """Finds all wc style link occurences in a given string"""
        matches = []
        for line in string.split(', '):
            match = re.match(cls.regex_wc_link, line)
            if match is None:
                continue
            match_dict = match.groupdict()
            if 'url' in match_dict and 'rel' in match_dict:
                matches.append(match_dict)
        return matches


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
        print [
            SanitationUtils.coerce_bytestr(x) for x in \
            [cls.get_caller_procedure(), message]
        ]

    @classmethod
    def register_error(cls, message):
        """Registers a message with warning severity and prints if verbose enough"""
        cls.register_message(message, cls.ERROR_VERBOSITY)

class ProgressCounter(object):
    def __init__(self, total, printThreshold=1):
        self.total = total
        self.printThreshold = printThreshold
        self.last_print = time.time()

    def maybe_print_update(self, count):
        now = time.time()
        if now - self.last_print > 1:
            self.last_print = now
            percentage = 0
            if self.total > 0:
                percentage = 100 * count / self.total
            DebugUtils.register_message(
                "({: >3}%%) {: >10} of {: >10} items processed".format(percentage, count, self.total)
            )

class DescriptorUtils:
    """Provides methods for creating properties and descriptors"""
    @staticmethod
    def safe_key_property(key_attr):
        def getter(self):
            assert hasattr(self, key_attr), "does not have attr: {}".format(key_attr)
            key = getattr(self, key_attr)
            assert key in self.keys(), "{} must be set before get".format(key)
            return self[key]

        def setter(self, value):
            assert hasattr(self, key_attr), "does not have attr: {}".format(key_attr)
            key = getattr(self, key_attr)
            assert \
                isinstance(value, (str, unicode)), \
                "{} must be set with string not {}".format(key, type(value))
            self[key] = value

        return property(getter, setter)
