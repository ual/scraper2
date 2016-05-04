from lxml import html
import requests

url = 'http://atlanta.craigslist.org/search/apa'

page = requests.get(url)
tree = html.fromstring(page.content)

# Each listing on the search results page is labeled as <p class="row">
listings = tree.xpath('//p[@class="row"]')

def readFromListing(item):

	pid = item.xpath('@data-pid')[0]  # post id
	
	# Extract two lines of listing info
	line1 = item.xpath('span[@class="txt"]/span[@class="pl"]')[0]
	line2 = item.xpath('span[@class="txt"]/span[@class="l2"]')[0]
	
	dt = line1.xpath('time/@datetime')[0]
	url = 'http://craigslist.org' + line1.xpath('a/@href')[0]
	title = line1.xpath('a/span/text()')[0]
	
	price = line2.xpath('span[@class="price"]/text()')[0].strip('$')
	neighb = line2.xpath('span[@class="pnr"]/small/text()')[0].strip(' ()')
	bedsqft = line2.xpath('span[@class="housing"]/text()')[0]
	
	beds = 0  # Bedrooms - appears as "1br" to "8br" or missing
	for s in bedsqft.split(' '):
		if 'br' in s:
			beds = s.strip('br')
	
	sqft = 0  # Square footage - appears as "000ft" or missing
	for s in bedsqft.split(' '):
		if 'ft' in s:
			sqft = s.strip('ft')

	source = ''  # FILL IN SEARCH SOURCE
	return [pid, dt, url, title, price, neighb, beds, sqft, source]


for item in listings[:2]:
	print readFromListing(item)




# stop traversing pages if post id is too old? - or only keep prev calendar day?


