from crawler import PageFetcher, Scheduler
from urllib.parse import urlparse
scheduler = Scheduler("batata-bot", page_limit=30, depth_limit=10, arr_urls_seeds=[urlparse("http://www.amazon.com/")])
pf = PageFetcher(scheduler)
pf.run()
