import unittest
import mock
import source.lib.__init__ as init
import re
from source import lib

def create_html(redirect, url = "", refresh = True):
    html = "<html><head>"
    if redirect:
        html += r'<meta '.format(url)
        if refresh:
            html += r'http-equiv="refresh" '.format(url)
        html += r'content="12345; url={0}">'.format(url)
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
    def test_check_for_meta_with_too_many_args(self):
        redirect = ";123;http://url.com"
        prefix = "http://url.com"
        html = create_html(True, redirect)
        result = init.check_for_meta(html, prefix)
        self.assertEqual(result, None)
        pass
    def test_check_for_meta_bad_url(self):
        redirect = "http://url.com"
        prefix = ""
        html = create_html(True)
        result = init.check_for_meta(html, prefix)
        self.assertEqual(result, None)
        pass
    def test_check_for_meta_with_no_refresh(self):
        redirect = "test.html"
        prefix = ";http://url.com"
        html = create_html(True, redirect, False)
        result = init.check_for_meta(html, prefix)
        self.assertEqual(result, None)
        pass

    def test_fix_market_url_with_market_url(self):
        url = "market://url.com"
        expected = "http://play.google.com/store/apps/url.com"
        result = init.fix_market_url(url)
        self.assertEqual(result, expected)
        pass
    def test_fix_market_url_with_no_market_url(self):
        url = "none://url.com"
        expected = "http://play.google.com/store/apps/" + url
        result = init.fix_market_url(url)
        self.assertEqual(result, expected)
        pass


    def test_make_pycurl_request(self):
        url = "http://url.com"
        timeout = "timeout"
        useragent = "useragent"
        curl = mock.Mock()
        io = mock.Mock()
        buff = "buff"
        url = "url"
        io.getvalue = mock.Mock(return_value=buff)
        curl.getinfo = mock.Mock(return_value=url)
        with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
            with mock.patch('source.lib.__init__.StringIO', mock.Mock(return_value=io)):
                result = init.make_pycurl_request(url, timeout, useragent)
        self.assertEqual(result, (buff, url))
        pass
    def test_make_pycurl_bad_request(self):
        url = "http://url.com"
        timeout = "timeout"
        curl = mock.Mock()
        io = mock.Mock()
        buff = "buff"
        url = None
        io.getvalue = mock.Mock(return_value=buff)
        curl.getinfo = mock.Mock(return_value=url)
        with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
            with mock.patch('source.lib.__init__.StringIO', mock.Mock(return_value=io)):
                result = init.make_pycurl_request(url, timeout)
        self.assertEqual(result, (buff, url))
        pass

    def test_get_url_market(self):
        url = "http://url.com"
        timeout = "timeout"
        useragent = "useragent"
        content = "content"
        redirect = "market://test.org"
        request_return = (content, redirect)
        result_url = "http://test.com"
        market_mock = mock.Mock(return_value=result_url);
        with mock.patch('source.lib.__init__.make_pycurl_request', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.fix_market_url', market_mock):
                result = init.get_url(url, timeout, useragent)
        self.assertEqual(result, (result_url, init.REDIRECT_HTTP, content))
        market_mock.assert_called_once_with(redirect)
        pass
    def test_get_url_meta(self):
        url = "http://url.com"
        timeout = "timeout"
        useragent = "useragent"
        content = "content"
        redirect = None
        request_return = (content, redirect)
        result_url = "http://test.com"
        meta_mock = mock.Mock(return_value=result_url);
        with mock.patch('source.lib.__init__.make_pycurl_request', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.check_for_meta', meta_mock):
                result = init.get_url(url, timeout, useragent)
        self.assertEqual(result, (result_url, init.REDIRECT_META, content))
        pass
    def test_get_url_login_redirect(self):
        url = "http://url.com"
        timeout = "timeout"
        useragent = "useragent"
        content = "content"
        redirect = "http://www.odnoklassniki.ru/st.redirect"
        request_return = (content, redirect)
        result_url = "http://test.com"
        meta_mock = mock.Mock(return_value=result_url);
        with mock.patch('source.lib.__init__.make_pycurl_request', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.check_for_meta', meta_mock):
                result = init.get_url(url, timeout, useragent)
        self.assertEqual(result, (None, None, content))
        pass
    def test_get_url_exeption(self):
        url = "http://url.com"
        timeout = "timeout"
        useragent = "useragent"
        exeption = ValueError("test exeption")
        with mock.patch('source.lib.__init__.make_pycurl_request', mock.Mock(side_effect=exeption)):
            with mock.patch('source.lib.__init__.logger.error', mock.Mock()):
                result = init.get_url(url, timeout, useragent)
        self.assertEqual(result, (url, 'ERROR', None))
        pass

    def test_get_redirect_history_ok_page(self):
        url = "http://www.odnoklassniki.ru/"
        timeout = "timeout"
        result = init.get_redirect_history(url, timeout)
        self.assertEqual(result, ([], [url], []))
        pass
    def test_get_redirect_history_zero_length(self):
        url = "http://url.com"
        timeout = "timeout"
        redirect_url = "redirect_url"
        redirect_type = "redirect_type"
        content = "content"
        counters = "counters"
        request_return = (redirect_url, redirect_type, content)
        with mock.patch('source.lib.__init__.get_url', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.get_counters', mock.Mock(return_value=counters)):
                result = init.get_redirect_history(url, timeout, 0)
        self.assertEqual(result, ([redirect_type], [url, redirect_url], counters))
        pass
    def test_get_redirect_history_error(self):
        url = "http://url.com"
        timeout = "timeout"
        redirect_url = "redirect_url"
        redirect_type = "ERROR"
        content = "content"
        counters = "counters"
        request_return = (redirect_url, redirect_type, content)
        with mock.patch('source.lib.__init__.get_url', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.get_counters', mock.Mock(return_value=counters)):
                result = init.get_redirect_history(url, timeout)
        self.assertEqual(result, ([redirect_type], [url, redirect_url], counters))
        pass
    def test_get_redirect_history_not_a_redirect(self):
        url = "http://url.com"
        timeout = "timeout"
        redirect_url = None
        redirect_type = "redirect_type"
        content = "content"
        counters = "counters"
        request_return = (redirect_url, redirect_type, content)
        with mock.patch('source.lib.__init__.get_url', mock.Mock(return_value=request_return)):
            with mock.patch('source.lib.__init__.get_counters', mock.Mock(return_value=counters)):
                result = init.get_redirect_history(url, timeout)
        self.assertEqual(result, ([], [url], counters))
        pass


    def test_prepare_url_none(self):
        url = None
        result = init.prepare_url(url)
        self.assertEqual(result,  url)
        pass
        
    def test_prepare_url_ok(self):
        url = "http://url.com/ a nice day to parce@#$%^/../"
        result = init.prepare_url(url)
        self.assertEqual(result,  "http://url.com/%20a%20nice%20day%20to%20parce%40%23$%%5E/../")
        pass
        
    def test_prepare_url_exeption(self):
        url = "http://url.com"
        exeption = UnicodeError("test error")
        with mock.patch('source.lib.__init__.urlparse', mock.Mock(side_effect=exeption)):
            self.assertRaises(UnicodeError, init.prepare_url, url)
        pass
