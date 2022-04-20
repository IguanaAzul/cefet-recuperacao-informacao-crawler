import time
import unittest
from urllib.parse import urlparse

from .domain import *
from .scheduler import *


class DomainTest(unittest.TestCase):

    def test_domain(self):
        domain = Domain("xpto.com", 10)
        self.assertTrue(domain.is_accessible(),
                        "Ao iniciar um servidor, ele deve estar acessível")

        domain.accessed_now()
        self.assertTrue(not domain.is_accessible(
        ), "Como ele acabou de ser acessado, ele não pode estar acessivel")
        print("Verificando acesso a um dominio já requisitado (após espera)")
        print("aguardando 10 segundos...")
        time.sleep(10)
        self.assertTrue(domain.is_accessible(),
                        f"Após a espera do tempo limite entre requisições, o servidor deveria voltar a ficar acessível")


class SchedulerTest(unittest.TestCase):
    urlXpto = (urlparse("https://www.xpto.com.br/index.html"), 100000)
    urlTerra = (urlparse("https://www.terra.com.br/index.html"), 1)
    urlTerra2 = (urlparse("https://www.terra.com.br/index.html"), 1)
    urlTerraRep = (urlparse("https://www.terra.com.br/index.html"), 1)
    urlUOL1 = (urlparse("https://www.uol.com.br/"), 1)
    urlUOL2 = (urlparse("https://www.uol.com.br/profMax.html"), 1)
    urlGlobo = (urlparse("https://www.globo.com.br/profMax.html"), 1)
    MOCK_USER_AGENT = 'azulaoBot'
    TIME_LIMIT = 10
    DEPTH_LIMIT = 3
    SEEDS = []

    def setUp(self):
        self.scheduler = Scheduler(usr_agent="xxbot",
                                   page_limit=self.TIME_LIMIT,
                                   depth_limit=self.DEPTH_LIMIT,
                                   arr_urls_seeds=self.SEEDS)

    def test_init(self):
        arr_str_urls_seeds = ["cnn.com",
                              "www.gq.com.au/", "www.huffingtonpost.com/"]
        arr_urls_seeds = [urlparse(str_url) for str_url in arr_str_urls_seeds]
        
        self.scheduler = Scheduler(usr_agent="xxbot",
                                   page_limit=self.TIME_LIMIT,
                                   depth_limit=self.DEPTH_LIMIT,
                                   arr_urls_seeds=arr_urls_seeds)
        
        self.assertEqual(len(arr_str_urls_seeds), self.scheduler.page_count, "Nao foi adicionado as sementes solicitadas")

    def test_can_add_page(self):
        self.__testCanAddPageWithLongTimeLimit()
        self.__test_existed_domain()

    def __testCanAddPageWithLongTimeLimit(self):
        if Scheduler.TIME_LIMIT_BETWEEN_REQUESTS < self.urlXpto[1]:
            canAddXpto = self.scheduler.can_add_page(*self.urlXpto)
            self.assertFalse(canAddXpto, msg='A url XPTO não deveria poder ser adicionada')

    def __test_existed_domain(self):
        scheduler_test = Scheduler(usr_agent=self.MOCK_USER_AGENT,
                                   page_limit=self.TIME_LIMIT,
                                   depth_limit=self.DEPTH_LIMIT,
                                   arr_urls_seeds=self.SEEDS)
        self.__test_can_add_uol1(scheduler_test)
        self.__add_uol_1(scheduler_test)
        self.__test_can_add_uol2(scheduler_test)

    def __add_uol_1(self, scheduler_test):
        domainUol1 = Domain(self.urlUOL1[0].hostname, Scheduler.TIME_LIMIT_BETWEEN_REQUESTS)
        scheduler_test.dic_url_per_domain[domainUol1] = [self.urlUOL1]

    def __test_can_add_uol1(self, scheduler_test):
        self.assertTrue(scheduler_test.can_add_page(*self.urlUOL1), msg='A URL do UOL1 deveria poder ser adicionada')

    def __test_can_add_uol2(self, scheduler_test):
        self.assertTrue(scheduler_test.can_add_page(*self.urlUOL2), msg='A URL do UOL2 deveria poder ser adicionada')

    def test_add_remove_page(self):
        self.test_can_add_page()
        # tuplas url,profundidade a serem testadas

        arr_urls = [self.urlXpto, self.urlTerra, self.urlTerraRep, self.urlUOL1, self.urlUOL2, self.urlGlobo]

        # adiciona todas as paginas em ordem
        # "**" faz passar a url e a profundidade
        # como o primeiro e segundo parametro, respectivamente
        [self.scheduler.add_new_page(*url) for url in arr_urls]
        # verificação se adicionou a mesma URL duas vezes
        urls = set()
        for key, arr in self.scheduler.dic_url_per_domain.items():
            set_urls = set(arr)
            self.assertTrue(len(set_urls) == len(
                arr), "Existem URLs repetidas na fila!")


        u1 = self.scheduler.get_next_url()
        u2 = self.scheduler.get_next_url()
        u3 = self.scheduler.get_next_url()
        # ao obter a UOL, é considerado a primeira requisição nela
        time_first_hit_UOL = datetime.now()

        print("Verificação da ordem das URLs...")
        arr_expected_order = [self.urlTerra[0], self.urlUOL1[0], self.urlGlobo[0]]
        arr_url_order = [u1[0], u2[0], u3[0]]
        for i, expected_url in enumerate(arr_expected_order):
            self.assertTrue(
                arr_url_order[i] is not None, msg=f"A {i + 1}ª URL não deveria ser none")
            self.assertEqual(expected_url, arr_url_order[i],
                             f"A URL {expected_url.geturl()} deveria ser a {i + 1}ª a ser obtida e foi a {arr_url_order[i].geturl()}.")

        # resgata o quarto (UOL)
        print("Resgatando a segunda página do mesmo dominio...")
        u4 = self.scheduler.get_next_url()

        time_second_hit_UOL = datetime.now()
        time_wait = (time_second_hit_UOL - time_first_hit_UOL)
        time_wait_seconds = time_wait.seconds
        if time_wait.microseconds > 500000:
            time_wait_seconds += 1

        print(f"Tempo esperado: {time_wait_seconds} segundos")
        self.assertTrue(time_wait_seconds >= Scheduler.TIME_LIMIT_BETWEEN_REQUESTS,
                        f"O tempo de espera entre as duas requisições do mesmo servidor não foi maior que {Scheduler.TIME_LIMIT_BETWEEN_REQUESTS} (foi {time_wait_seconds} segundos)")


    def test_can_fetch(self):
        obj_url_not_allowed = urlparse('https://www.globo.com/beta/dasdas')
        obj_url_allowed = urlparse('https://www.terra.com/index.html')

        bol_not_allowed = self.scheduler.can_fetch_page(obj_url_not_allowed)
        bol_allowed = self.scheduler.can_fetch_page(obj_url_allowed)

        self.assertTrue(obj_url_not_allowed.netloc in self.scheduler.dic_robots_per_domain,
                        msg=f"O domínio '{obj_url_not_allowed.netloc}' não foi encontrado")
        obj_robot_not_allowed = self.scheduler.dic_robots_per_domain[obj_url_not_allowed.netloc]

        # verifica se, nas requisições, o robot retornou a resposta correta
        self.assertTrue(not bol_not_allowed,
                        f"Não deveria ser permitida requisitar a url {obj_url_not_allowed.geturl()} segundo o robots.txt  do dominio {obj_url_not_allowed.netloc}, porém o método can_fetch_page retornou True")
        self.assertTrue(bol_allowed,
                        f"Deveria ser permitida requisitar a url {obj_url_allowed.geturl()} segundo o robots.txt do dominio {obj_url_allowed.netloc}, porém o método can_fetch_page retornou False")

        # verifica se foi adicionado a globo.com
        self.assertTrue(obj_url_allowed.netloc in self.scheduler.dic_robots_per_domain,
                        "Não foi adicionado o robot da globo.com em dic_robots_per_domain do escalonador")

        # verifica se foi usado o mesmo robot
        self.scheduler.can_fetch_page(obj_url_not_allowed)
        self.assertTrue(obj_robot_not_allowed == self.scheduler.dic_robots_per_domain[obj_url_not_allowed.netloc],
                        "Na segunda requisição de um mesmo dominio, você não pode criar um novo objeto RobotFileParser")

        self.assertTrue(
            bol_allowed, f"O mesmo robots.txt não pode ser requisitado duas vezes.")



if __name__ == "__main__":
    unittest.main()
