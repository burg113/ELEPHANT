import unittest
from werkzeug import exceptions
from main import check_cal_url


whitelist = {
        "campus.kit.edu": {
            "scheme": ["http", "https"],
            "path": ["/sp/webcal/"],
        }
    }

class check_cal_url_TEST(unittest.TestCase):
    def test_urls(self):

        self.assertRaises(exceptions.Forbidden, check_cal_url, "abc://example.com", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "http://example.com", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "https://example.com", whitelist)

        self.assertRaises(exceptions.Forbidden, check_cal_url, "abc://kit.edu", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "http://kit.edu", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "https://kit.edu", whitelist)

        self.assertRaises(exceptions.Forbidden, check_cal_url, "abc://campus.kit.edu", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "http://campus.kit.edu", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "https://campus.kit.edu", whitelist)

        self.assertRaises(exceptions.Forbidden, check_cal_url, "abc://campus.kit.edu/test", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "http://campus.kit.edu/test", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "https://campus.kit.edu/test", whitelist)


        self.assertRaises(exceptions.Forbidden, check_cal_url, "http://campus.kit.edu/sp/webcal/abc/../..", whitelist)
        self.assertRaises(exceptions.Forbidden, check_cal_url, "https://campus.kit.edu/sp/webcal/abc/../..", whitelist)

        # Test path traversal
        self.assertRaises(exceptions.Forbidden, check_cal_url, "abc://campus.kit.edu/sp/webcal/abc", whitelist)

        self.assertTrue(exceptions.Forbidden, check_cal_url("http://campus.kit.edu/sp/webcal/abc", whitelist))
        self.assertTrue(exceptions.Forbidden, check_cal_url("https://campus.kit.edu/sp/webcal/abc", whitelist))

