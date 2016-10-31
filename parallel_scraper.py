# This is a test script for the rental listing scraper
from datetime import datetime as dt
from datetime import timedelta
import time
import sys
sys.path.insert(0, 'scraper2/')
import scraper2
import multiprocessing


__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"

# add subfolder to system path

domains = []
with open('domains.txt', 'rb') as f:
    for line in f.readlines():
        domains.append((line.strip()))

lookback = 2  # hours

earliest_ts = dt.now() - timedelta(hours=lookback)
latest_ts = dt.now() + timedelta(hours=0)

jobs = []

st_time = time.time()
for domain in domains:
    s = scraper2.RentalListingScraper(
        domains=[domain],
        earliest_ts=earliest_ts,
        latest_ts=latest_ts)
    print 'Starting process for ' + domain
    p = multiprocessing.Process(target=s.run)
    jobs.append(p)
    p.start()

for i, job in enumerate(jobs):
    job.join()
    end_time = time.time()
    elapsed_time = end_time - st_time
    time_per_domain = elapsed_time / (i + 1.0)
    num_domains = len(jobs)
    domains_left = num_domains - (i + 1.0)
    time_left = domains_left * time_per_domain
    print("Took {0} seconds for {1} regions.".format(elapsed_time, i + 1))
    print("About {0} seconds left.".format(time_left))
