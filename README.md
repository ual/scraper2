# Scraper2

Streamlined web crawler for rental listings


### What it does

The `scraper2` directory defines a generalized Craigslist rental listing crawler, and scripts like `test_scraper.py` and `scrape_prior_day.py` instantiate it with particular lists of search domains, time parameters, and other settings. 

Functionality is similar to `ClistRentScraper` (developed by Geoff in 2014), but the operations are now defined explicitly rather than as `Scrapy` projects. This should make the crawler easier to maintain and debug. We use the `Requests` library for HTTP requests and `Lxml` to parse webpage content. 

The crawler begins by loading a page of Craigslist search results, for example http://sfbay.craigslist.org/search/apa. From that page, it parses each listing's title, url, price, characteristics, and timestamp. Next, it visits each listing url to extract addresses and lat-lon coordinates. Then it moves on to the next page of search results and repeats the process. 

The data is saved to a CSV file, and diagnostics and errors are saved to a log file.

`ClistRentScraper` only kept lat-lon coordinates, but Craigslist listings now also include a location accuracy indicator and an address or cross streets, when users have provided it. `Scraper2` saves this data for future analysis.


### Status

This project is on hold while we look into more official access to Craigslist data.


### Task list (higher priority)

- Figure out what Craigslist's throttle thresholds are, and put rate limits into our scripts. On 5/6 they blocked my IP after requesting about 10,000 URLs over a few hours.

- Add a filter to avoid requesting URLs for listings that we know from the results page are missing necessary variables like price or number of bedrooms.

- Add docstrings and other proper code templating.

- Deploy on Linux server.

- Add option to upload data to S3.

- Add Slack status notification.

- Write unit tests.

- Craigslist returns a maximum of 2500 search results per query, which in high-traffic regions is much less than a full day of listings. For example, it's approx 6 daytime hours in the "sfbay" region. Here are some options: (a) run the scraper once a day at midnight and accept that we are getting an incomplete sample (current approach), (b) run the scraper more frequently, (c) try switching to sub-region searches.


### Task list (lower priority)

- Improve log messages.

- Improve and test the fail conditions to make sure we won't get into recursive loops, and exit quickly when Craigslist throttles our requests.

- Is the list of data fields we're collecting optimal? 

- Check the master list of Craigslist domains that we're crawling, which was compiled by Geoff in 2014. Is there a way to assemble the list programmatically, to make sure it's always up to date?

- Should we put the rental listings directly into a database as well as flat files?

- Develop a separate set of scripts for data cleaning, for example to remove duplicate listings.
