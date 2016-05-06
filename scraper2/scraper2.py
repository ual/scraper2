__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"

from datetime import datetime as dt
from datetime import timedelta
import logging
import urllib
import unicodecsv as csv
from lxml import html
import requests


# Some defaults, which can be overridden when the class is called

DOMAINS = ['http://sfbay.craigslist.org']  # List of regional domains to search

# Craigslist doesn't use time zones in its timestamps, so these cutoffs will be
# interpreted relative to the local time at the listing location. For example, dt.now()
# run from a machine in San Francisco will match listings from 3 hours ago in Boston.
EARLIEST_TS = dt.now() - timedelta(hours=0.25)
LATEST_TS = dt.now()

OUT_DIR = 'data/'
FNAME_BASE = 'data-'  # filename prefix (timestamp and filetype extension will be appended)
S3_UPLOAD = False
S3_BUCKET = 'scraper2'


class RentalListingScraper(object):

	def __init__(
			self, 
			domains = DOMAINS,
			earliest_ts = EARLIEST_TS,
			latest_ts = LATEST_TS, 
			out_dir = OUT_DIR,
			fname_base = FNAME_BASE,
			s3_upload = S3_UPLOAD,
			s3_bucket = S3_BUCKET):
		
		self.domains = domains
		self.earliest_ts = earliest_ts
		self.latest_ts = latest_ts
		self.out_dir = out_dir
		self.fname_base = fname_base
		self.s3_upload = s3_upload
		self.s3_bucket = s3_bucket
		
		self.ts = dt.now().strftime('%Y%m%d-%H%M%S')  # Use as id for outfile and logfile
		logging.basicConfig(filename='logs/' + self.ts + '.log', level=logging.INFO)
		# Suppress info messages from the 'requests' library
		logging.getLogger('requests').setLevel(logging.WARNING)  


	def _get_str(self, list):
		'''
		The xpath() function returns a list of items that may be empty. Most of the time,
		we want the first of any strings that match the xml query. This helper function
		returns that string, or null if the list is empty.
		'''
		
		if len(list) > 0:
			return list[0]

		return ''
	
	
	def _get_int_prefix(self, str, label):
		'''
		Bedrooms and square footage have the format "xx 1br xx 450ft xx". This helper 
		function extracts relevant integers from strings of this format.
		'''		
		
		for s in str.split(' '):
			if label in s:
				return s.strip(label)
				
		return 0
		

	def _parseListing(self, item):
		'''
		Note that xpath() returns a list with elements of varying types depending on the
		query results: xml objects, strings, etc.
		'''
	
		pid = item.xpath('@data-pid')[0]  # post id, always present
	
		# Extract two lines of listing info, always present
		line1 = item.xpath('span[@class="txt"]/span[@class="pl"]')[0]
		line2 = item.xpath('span[@class="txt"]/span[@class="l2"]')[0]
	
		dt = line1.xpath('time/@datetime')[0]  # always present
		url = line1.xpath('a/@href')[0]  # always present
		title = self._get_str(line1.xpath('a/span/text()'))
	
		price = self._get_str(line2.xpath('span[@class="price"]/text()')).strip('$')
		neighb = self._get_str(line2.xpath('span[@class="pnr"]/small/text()')).strip(' ()')
		bedsqft = self._get_str(line2.xpath('span[@class="housing"]/text()'))
	
		beds = self._get_int_prefix(bedsqft, "br")  # appears as "1br" to "8br" or missing
		sqft = self._get_int_prefix(bedsqft, "ft")  # appears as "000ft" or missing
		
		return [pid, dt, url, title, price, neighb, beds, sqft]
		

	def _parseAddress(self, tree):
		'''
		Some listings include an address, but we have to parse it out of an encoded
		Google Maps url.
		'''
		url = self._get_str(tree.xpath('//p[@class="mapaddress"]/small/a/@href'))
		
		if '?q=loc' not in url:
			# That string precedes an address search
			return ''
			
		return urllib.unquote_plus(url.split('?q=loc')[1]).strip(' :')

	
	def _scrapeLatLng(self, url):
	
		page = requests.get(url)
		tree = html.fromstring(page.content)
		
		map = tree.xpath('//div[@id="map"]')

		# Sometimes there's no location info, and no map on the page		
		if len(map) == 0:
			return ['', '', '', '']

		map = map[0]
		lat = map.xpath('@data-latitude')[0]
		lng = map.xpath('@data-longitude')[0]
		accuracy = map.xpath('@data-accuracy')[0]
		address = self._parseAddress(tree)
		
		return [lat, lng, accuracy, address]
		
	
	def run(self):
	
		colnames = ['pid','dt','url','title','price','neighb','beds','sqft',
						'lat','lng','accuracy','address']

		fname = self.out_dir + self.fname_base + self.ts + '.csv'
		with open(fname, 'wb') as f:
			writer = csv.writer(f)
			writer.writerow(colnames)

			# Loop over each regional Craigslist URL
			for domain in self.domains:	
				regionIsComplete = False
				logging.info('BEGINNING SEARCH OF ' + domain )
				page = requests.get(domain + '/search/apa')  # Initial page of search results
				
				while not regionIsComplete:
					tree = html.fromstring(page.content)
					# Each listing on the search results page is labeled as <p class="row">
					listings = tree.xpath('//p[@class="row"]')

					for item in listings:
						try:
							row = self._parseListing(item)
							item_ts = dt.strptime(row[1], '%Y-%m-%d %H:%M')
				
							if (item_ts > self.latest_ts):
								# Skip this item but continue parsing search results
								continue  
					
							if (item_ts < self.earliest_ts):
								# Break out of loop and move on to the next region
								regionIsComplete = True
								break 
					
							item_url = domain + row[2]
							row[2] = item_url
							row += self._scrapeLatLng(item_url)				
							writer.writerow(row)
							
						except Exception, e:
							# Catch any problems parsing a listing
							if len(row) > 0:
								logging.info('ERROR PARSING ' + item_url)
							logging.info("%s: %s" % (type(e).__name__, e))
							continue
						
					# Go to the next search results page
					next = tree.xpath('//a[@title="next page"]/@href')
					if len(next) > 0:
						logging.info(domain + next[0])
						page = requests.get(domain + next[0])
					else:
						regionIsComplete = True
							
		return











