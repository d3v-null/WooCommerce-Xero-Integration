import inspect
import re
import os
from os import path, sys

from kitchen.text import converters

class SanitationUtils:
    regex_url = r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)"
    regex_wc_link = r"<(?P<url>{0})>; rel=\"(?P<rel>\w+)\"".format(regex_url)

    @staticmethod
    def wrap_full_match(regex):
        return r"${}^".format(regex)

    @staticmethod
    def wrap_paren(regex):
        return r"({})".format(regex)

    @classmethod
    def coerceUnicode(self, thing):
        if thing is None:
            unicode_return = u""
        else:
            unicode_return = converters.to_unicode(thing, encoding="utf8")
        assert isinstance(unicode_return, unicode), "something went wrong, should return unicode not %s" % type(unicode_return)
        return unicode_return

    @classmethod
    def findall_wc_link(self, string):
        pass

class ValidationUtils:
    @staticmethod
    def isNotNone(value):
        if value is None:
            return "must not be None"

    @staticmethod
    def isFile(value):
        if not os.path.isfile(value):
            return "must be a file"

    @staticmethod
    def isUrl(value):
        pass


class DebugUtils:
    ERROR_VERBOSITY = 1
    WARNING_VERBOSITY = 2
    MESSAGE_VERBOSITY = 3

    @staticmethod
    def getProcedure():
        return inspect.stack()[1][3]

    @staticmethod
    def getCallerProcedure():
        return inspect.stack()[2][3]

    @classmethod
    def registerMessage(self, message, severity=None):
        if severity is None:
            severity = self.MESSAGE_VERBOSITY
        print self.getProcedure(), message

    @classmethod
    def registerError(self, message):
        self.registerMessage(message, self.ERROR_VERBOSITY)
