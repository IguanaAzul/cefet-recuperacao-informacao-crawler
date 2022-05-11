import urllib.error
from typing import Optional

from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse, urljoin, ParseResult


class PageFetcher(Thread):
    USER_AGENT = 'pseudoBot'

    def __init__(self, obj_scheduler):
        super().__init__()
        self.obj_scheduler = obj_scheduler

    def request_url(self, obj_url: ParseResult) -> Optional[bytes] or None:
        """
        :param obj_url: Instância da classe ParseResult com a URL a ser requisitada.
        :return: Conteúdo em binário da URL passada como parâmetro, ou None se o conteúdo não for HTML
        """

        response = requests.get(obj_url.geturl(), headers={'User-Agent': self.USER_AGENT})
        if 'text/html' in response.headers['Content-Type']:
            return response.content
        else:
            return None

    def discover_links(self, obj_url: ParseResult, depth: int, bin_str_content: bytes):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content, features="lxml")
        for link in soup.select("a[href]"):
            try:
                obj_new_url = urlparse(urljoin(obj_url.geturl(), link.get('href')))
            except urllib.error.URLError:
                continue
            new_depth = 0 if obj_url.netloc != obj_new_url.netloc else depth + 1
            if self.obj_scheduler.can_add_page(obj_new_url, new_depth):
                self.obj_scheduler.add_new_page(obj_new_url, new_depth)
                # print(obj_new_url.geturl(), new_depth, obj_url.geturl())
            # yield obj_new_url, new_depth

    def crawl_new_url(self):
        """
        Coleta uma nova URL, obtendo-a do escalonador
        """
        obj_url = self.obj_scheduler.get_next_url()
        if obj_url:
            if self.obj_scheduler.can_fetch_page(obj_url[0]):
                response = self.request_url(obj_url[0])
                if response:
                    # print(obj_url)
                    self.discover_links(obj_url[0], obj_url[1], response)
                    self.obj_scheduler.count_fetched_page()

    def run(self):
        """
        Executa coleta enquanto houver páginas a serem coletadas
        """
        while not self.obj_scheduler.has_finished_crawl():
            self.crawl_new_url()
