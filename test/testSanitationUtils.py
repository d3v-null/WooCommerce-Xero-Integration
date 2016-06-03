# coding=utf-8

from os import sys, path
from unittest import TestCase, main, skip
import re

if __name__ == '__main__' and __package__ is None:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from src.utils import SanitationUtils

class TestSanitationUtils(TestCase):
    def test_coerce_unicode(self):
        coerce_none = SanitationUtils.coerce_unicode(None)
        self.assertEqual(coerce_none, u'')
        self.assertIsInstance(coerce_none, unicode)

        coerce_bytestr = SanitationUtils.coerce_unicode('asdf\xe7')
        self.assertEqual(u'asdf\ufffd', coerce_bytestr)
        self.assertIsInstance(coerce_bytestr, unicode)

    def test_maybe_wrap_full_match(self):
        self.assertEqual(
            SanitationUtils.maybe_wrap_full_match('asdf'),
            '^asdf$'
        )
        self.assertEqual(
            SanitationUtils.maybe_wrap_full_match('^asf$'),
            '^asf$'
        )

    def test_url_regex(self):
        match = re.match(
            (SanitationUtils.regex_url),
            'http://www.laserphile.com/asdf/df?filter[param]=true&sdf=g'
        )
        self.assertEqual(
            match.group(0),
            'http://www.laserphile.com/asdf/df?filter[param]=true&sdf=g'
        )
        match = re.match(
            (SanitationUtils.regex_url),
            'http://www.laserphile.com/'
        )
        self.assertEqual( match.group(0), 'http://www.laserphile.com/')


    def test_findall_wc_links(self):
        results = SanitationUtils.findall_wc_links(
            '<http://www.annachandler.com/wc-api/v3/products?filter[meta]=true'+
            '&oauth_consumer_key=ck_ed0a5ae4658a895dbdf6e4009d81a850e1ec3347'+
            '&oauth_timestamp=1464927585&oauth_nonce=f8bbaf5c3795d1e7dd76112f5290465301e2a7d6'+
            '&oauth_signature_method=HMAC-SHA256'+
            '&oauth_signature=WsQCgHfubKIHHRkKS3879NwzQEImMPcHEtxh8aiBg7A=&page=2>; rel="next", '
            '<http://www.annachandler.com/wc-api/v3/products?filter[meta]=true'+
            '&oauth_consumer_key=ck_ed0a5ae4658a895dbdf6e4009d81a850e1ec3347'+
            '&oauth_timestamp=1464927585&oauth_nonce=f8bbaf5c3795d1e7dd76112f5290465301e2a7d6'+
            '&oauth_signature_method=HMAC-SHA256&'+
            'oauth_signature=WsQCgHfubKIHHRkKS3879NwzQEImMPcHEtxh8aiBg7A=&page=31>; rel="last"'
        )
        print results

if __name__ == '__main__':
    main()
