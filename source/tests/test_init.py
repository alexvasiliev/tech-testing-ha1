import unittest
import mock
import source.lib.__init__ as init
import re
from source import lib

def create_html(redirect, url = ""):
    html = "<html><head>"
    if redirect:
        html += r"""<meta http-equiv="refresh" content="12345; url={0}">""".format(url)
    html += "</head><body></body></html>"
    return html

class InitTestCase(unittest.TestCase):
    def test_to_unicode_unicode(self):
        text = u"text"
        result = init.to_unicode(text)
        self.assertTrue(isinstance(result, unicode))
        pass
    def test_to_unicode_not_unicode(self):
        text = "text"
        result = init.to_unicode(text)
        self.assertTrue(isinstance(result, unicode))
        pass


    def test_to_str_unicode(self):
        text = u"text"
        result = init.to_str(text)
        self.assertTrue(isinstance(result, str))
        pass
    def test_to_str__not_unicode(self):
        text = "text"
        result = init.to_str(text)
        self.assertTrue(isinstance(result, str))
        pass

    def test_get_counters_nothing(self):
        content = ""
        result = init.get_counters(content)
        self.assertEqual(result, [])
        pass
    def test_get_counters_google(self):
        content = "SOME_GARBAGE_google-analytics.com/ga.js_SOME_GARBAGE"
        result = init.get_counters(content)
        self.assertEqual(result, ['GOOGLE_ANALYTICS'])
        pass
    def test_get_counters_google_and_rambler(self):
        content = "SOME_GARBAGE_google-analytics.com/ga.js_SOME_GARBAGE"
        content += "SOME_GARBAGE_counter.rambler.ru/top100_SOME_GARBAGE"
        result = init.get_counters(content)
        self.assertEqual(result, ['GOOGLE_ANALYTICS', 'RAMBLER_TOP100'])
        pass


    def test_check_for_meta_with_redirect(self):
        redirect = "test.html"
        prefix = "http://url.com"
        expected = prefix + "/" + redirect
        html = create_html(True, redirect)
        result = init.check_for_meta(html, prefix)
        self.assertEqual(result, expected)
        pass
    def test_check_for_meta_with_no_redirect(self):
        prefix = "http://url.com"
        html = create_html(False)
        result = init.check_for_meta(html, prefix)
        self.assertEqual(result, None)
        pass

    def test_fix_market_url_with_market_url(self):
        url = "market://url.com"
        expected = "http://play.google.com/store/apps/url.com"
        result = init.fix_market_url(url)
        self.assertEqual(result, expected)
        pass


    #def test_make_pycurl_request(self):
    #    url = "http://url.com"
    #    timeout = "timeout"
    #    useragent = "useragent"
    #    curl = mock.Mock()
    #    io = mock.Mock()
    #    io.getvalue = mock.Mock(return_value="buff")
    #    curl.getinfo = mock.Mock(return_value="url")
    #    with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
    #        with mock.patch('StringIO.StringIO', mock.Mock(return_value=io)):
    #            result = init.make_pycurl_request(url, timeout, useragent)

    #    print result
    #    pass