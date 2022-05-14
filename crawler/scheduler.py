from urllib import robotparser
from urllib.parse import ParseResult
from xml import dom
from urllib.parse import urlparse
from util.threads import synchronized
from time import sleep
from collections import OrderedDict
from .domain import Domain

class Scheduler:
    # tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 5

    def __init__(self, usr_agent: str, page_limit: int, depth_limit: int, arr_urls_seeds):
        """
        :param usr_agent: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
        :param page_limit: Número de páginas a serem coletadas
        :param depth_limit: Profundidade máxima a ser coletada
        :param arr_urls_seeds: ?

        Demais atributos:
        - `page_count`: Quantidade de página já coletada
        - `dic_url_per_domain`: Fila de URLs por domínio (explicado anteriormente)
        - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
        - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas no `robots.txt`
        """
        self.usr_agent = usr_agent
        self.page_limit = page_limit
        self.depth_limit = depth_limit
        self.page_count = 0

        self.dic_url_per_domain = OrderedDict()
        self.set_discovered_urls = set()
        self.dic_robots_per_domain = {}
        for url in arr_urls_seeds:
            if self.add_new_page(url, 0):
                self.count_fetched_page()

    @synchronized
    def count_fetched_page(self) -> None:
        """
        Contabiliza o número de paginas já coletadas
        """
        self.page_count += 1

    def has_finished_crawl(self) -> bool:
        """
        :return: True se finalizou a coleta. False caso contrário.
        """
        if self.page_count >= self.page_limit:
            return True
        return False

    @synchronized
    def can_add_page(self, obj_url: ParseResult, depth: int) -> bool:
        """
        :return: True caso a profundidade for menor que a maxima e a url não foi descoberta ainda. False caso contrário.
        """
        return depth < self.depth_limit and obj_url.geturl() not in self.set_discovered_urls

    @synchronized
    def add_new_page(self, obj_url: ParseResult, depth: int) -> bool:
        """
        Adiciona uma nova página
        :param obj_url: Objeto da classe ParseResult com a URL a ser adicionada
        :param depth: Profundidade na qual foi coletada essa URL
        :return: True caso a página foi adicionada. False caso contrário
        """
        # https://docs.python.org/3/library/urllib.parse.html
        if self.can_add_page(obj_url, depth):
            if obj_url.netloc not in self.dic_url_per_domain.keys():
                self.dic_url_per_domain[
                    Domain(obj_url.netloc, self.TIME_LIMIT_BETWEEN_REQUESTS)] = list()
            self.dic_url_per_domain[obj_url.netloc].append((obj_url, depth))
            self.set_discovered_urls.add(obj_url.geturl())
            return True
        else:
            return False

    @synchronized
    def get_next_url(self) -> tuple:
        """
        Obtém uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """
        for domain, pages in self.dic_url_per_domain.items():
            if domain.is_accessible():
                domain.accessed_now()
                obj_url = pages.pop(0)
                if not pages:
                    self.dic_url_per_domain.pop(domain)
                return obj_url
        sleep(self.TIME_LIMIT_BETWEEN_REQUESTS / 10)    # Remover a divisão por 10 para passar no teste

    def can_fetch_page(self, obj_url: ParseResult) -> bool:
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        """
        url = obj_url.geturl()
        if not (urlparse(url).netloc in self.dic_robots_per_domain.keys()):
            rp = robotparser.RobotFileParser()
            rp.set_url(url)
            try:
                rp.read()
            except Exception as e:
                print(f"A url '{url}' não foi coletada, a seguinte exceção foi lançada:\n{type(e)}: {e}")
                return False
            self.dic_robots_per_domain[urlparse(url).netloc] = rp.can_fetch("*", url)
        return self.dic_robots_per_domain[urlparse(url).netloc]
