from crawler import PageFetcher, Scheduler
from urllib.parse import urlparse
scheduler = Scheduler("batata-bot", page_limit=30, depth_limit=3, arr_urls_seeds=[urlparse("http://www.amazon.com.br/")])
n_threads = 5
threads = list()
for t in range(n_threads):
    pf = PageFetcher(scheduler)
    pf.start()
    threads.append(pf)
for thread in threads:
    thread.join()
