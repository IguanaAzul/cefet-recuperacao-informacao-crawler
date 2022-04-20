import unittest
from urllib.parse import urlparse
import time
from .scheduler import *
from .page_fetcher import *


class PageFetcherTest(unittest.TestCase):
    def setUp(self):
        arr_urls_seeds = []
        self.scheduler = Scheduler(usr_agent="xxbot",
                                   page_limit=10,
                                   depth_limit=3,
                                   arr_urls_seeds=arr_urls_seeds)
        self.fetcher = PageFetcher(self.scheduler)

    def test_request_url(self):
        obj_url_google = urlparse('https://www.google.com.br')
        obj_not_html = urlparse('https://code.jquery.com/jquery-3.4.1.js')
        strb_google = self.fetcher.request_url(obj_url_google)
        strb_jquery = self.fetcher.request_url(obj_not_html)
        self.assertIsNotNone(strb_google, f'Não foi possível obter a URL: {obj_url_google.geturl()}')
        self.assertTrue(type(strb_google) == bytes, f'Ao requisitar uma URL válida, o tipo retornado deveria ser bytes')
        self.assertIsNone(strb_jquery, 'Ao ser requisitado alguma URL de um recurso que não é HTML, deve-se retornar None')

    def test_discover_links(self):
        obj_url = urlparse("http://www.pudim.com.br")
        bin_str_content = b"oi<a href='https://www.pudim.com.br/lala.html'></a>\
                              <a href='xxi/lala.html'></a>\
                             <a href='http://www.terra.com.br/oi/lala.html'></a>"

        arr_expected_links = [(urlparse('http://www.pudim.com.br/lala.html'), 3),
                              (urlparse('http://www.pudim.com.br/xxi/lala.html'), 3),
                              (urlparse('http://www.terra.com.br/oi/lala.html'), 0)
                              ]
        print(f"Simulação da extração de links da página {obj_url.geturl()} na profundidade nível 2...")
        for i,(url_link,depth) in enumerate(self.fetcher.discover_links(obj_url,2,bin_str_content)):
            self.assertEqual(arr_expected_links[i][0].geturl(),url_link.geturl(),f"A {i + 1}ª URL extraída seria {arr_expected_links[i][0].geturl()} e não {url_link.geturl()}")
            self.assertEqual(arr_expected_links[i][1],depth,f"A profundiade da URL {arr_expected_links[i][0].geturl()} seria {arr_expected_links[i][1]} e não {depth}")

if __name__ == "__main__":
    unittest.main()
