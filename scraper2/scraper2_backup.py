from __future__ import division
from datetime import datetime as dt
from datetime import timedelta
import logging
import urllib
import unicodecsv as csv
from lxml import html
import requests
import time
import sys
from requests.auth import HTTPProxyAuth
import pandas as pd
import numpy as np
import json
import psycopg2
import shutil
import os
import glob
import subprocess

# Some defaults, which can be overridden when the class is called

DOMAINS = ['http://sfbay.craigslist.org','http://modesto.craigslist.org/search/apa',
           'http://olympic.craigslist.org/search/apa']

# Craigslist doesn't use time zones in its timestamps, so these cutoffs will be
# interpreted relative to the local time at the listing location. For example, dt.now()
# run from a machine in San Francisco will match listings from 3 hours ago in Boston.
EARLIEST_TS = dt.now() - timedelta(hours=0.25)
LATEST_TS = dt.now()

OUT_DIR = '/home/mgardner/scraper2/data/'
FNAME_BASE = 'data-'  # filename prefix for saved data
FNAME_TS = True  # append timestamp to filename

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
            fname_ts = FNAME_TS,
            s3_upload = S3_UPLOAD,
            s3_bucket = S3_BUCKET):
        
        self.domains = domains
        self.earliest_ts = earliest_ts
        self.latest_ts = latest_ts
        self.out_dir = out_dir
        self.fname_base = fname_base
        self.fname_ts = fname_ts
        self.s3_upload = s3_upload
        self.s3_bucket = s3_bucket
        self.ts = fname_ts  # Use timestamp as file id

        log_fname = '/home/mgardner/scraper2/logs/' + self.fname_base \
                + (self.ts if self.fname_ts else '') + '.log'
        logging.basicConfig(filename=log_fname, level=logging.INFO)
        
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


    def _toFloat(self, string_value):
        string_value = string_value.strip()
        return np.float(string_value) if string_value else np.nan
        

    def _parseListing(self, item):
        '''
        Note that xpath() returns a list with elements of varying types depending on the
        query results: xml objects, strings, etc.
        '''
        pid = item.xpath('@data-pid')[0]  # post id, always present
        info = item.xpath('p[@class="result-info"]')[0]
        dt = info.xpath('time/@datetime')[0]
        url = info.xpath('a/@href')[0]
        if type(info.xpath('a/text()')) == str:
            title = info.xpath('a/text()')
        else:
            title = info.xpath('a/text()')[0]
        price = self._get_str(info.xpath('span[@class="result-meta"]/span[@class="result-price"]/text()')).strip('$')
        neighb_raw = info.xpath('span[@class="result-meta"]/span[@class="result-hood"]/text()')
        if len(neighb_raw) == 0:
            neighb = ''
        else:
            neighb = neighb_raw[0].strip(" ").strip("(").strip(")")
        housing_raw = info.xpath('span[@class="result-meta"]/span[@class="housing"]/text()')
        if len(housing_raw) == 0:
            beds = 0
            sqft = 0
        else:
            bedsqft = housing_raw[0]
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

    
    def _scrapeLatLng(self, session, url, proxy=True):
    
        s = session
        # if proxy:
        #     requests.packages.urllib3.disable_warnings()
        #     authenticator = '87783015bbe2d2f900e2f8be352c414a'
        #     proxy_str = 'http://' + authenticator + '@' +'workdistribute.charityengine.com:20000'
        #     s.proxies = {'http': proxy_str, 'https': proxy_str}
        #     s.auth = HTTPProxyAuth(authenticator,'') 

        page = s.get(url, timeout=30)
        tree = html.fromstring(page.content)
        try:
            baths = tree.xpath('//p[@class = "attrgroup"]//b')[1].text[:-2]
        except:
            baths = ''
        map = tree.xpath('//div[@id="map"]')

        # Sometimes there's no location info, and no map on the page        
        if len(map) == 0:
            return [baths,'', '', '', '']

        map = map[0]
        lat = map.xpath('@data-latitude')[0]
        lng = map.xpath('@data-longitude')[0]
        accuracy = map.xpath('@data-accuracy')[0]
        address = self._parseAddress(tree)
        
        return [baths, lat, lng, accuracy, address]


    def _get_fips(self, row):

            url = 'http://data.fcc.gov/api/block/find?format=json&latitude={}&longitude={}'
            request = url.format(row['latitude'], row['longitude'])

            # TO DO: exception handling
            response = requests.get(request)
            data = response.json()
            return pd.Series({'fips_block':data['Block']['FIPS'], 'state':data['State']['code'], 'county':data['County']['name']})


    def _clean_listings(self, filename):

        converters = {'neighb':str, 
              'title':str, 
              'price':self._toFloat, 
              'beds':self._toFloat,
              'baths':self._toFloat, 
              'pid':str, 
              'dt':str, 
              'url':str, 
              'sqft':self._toFloat, 
              'sourcepage':str, 
              'lng':self._toFloat, 
              'lat':self._toFloat}

        all_listings = pd.read_csv(filename, converters=converters)

        if len(all_listings) == 0:
            return [], 0, 0, 0
        # print('{0} total listings'.format(len(all_listings)))
        all_listings = all_listings.rename(columns={'price':'rent', 'dt':'date', 'beds':'bedrooms', 'neighb':'neighborhood',
                                                    'baths':'bathrooms','lng':'longitude', 'lat':'latitude'})
        all_listings['rent_sqft'] = all_listings['rent'] / all_listings['sqft']
        all_listings['date'] = pd.to_datetime(all_listings['date'], format='%Y-%m-%d')
        all_listings['day_of_week'] = all_listings['date'].apply(lambda x: x.weekday())
        all_listings['region'] = all_listings['url'].str.extract('http://(.*).craigslist.org', expand=False)
        unique_listings = pd.DataFrame(all_listings.drop_duplicates(subset='pid', inplace=False))
        thorough_listings = pd.DataFrame(unique_listings)
        thorough_listings = thorough_listings[thorough_listings['rent'] > 0]
        thorough_listings = thorough_listings[thorough_listings['sqft'] > 0]
        if len(thorough_listings) == 0:
            return [], 0, 0, 0

        # print('{0} thorough listings'.format(len(thorough_listings)))
        geolocated_filtered_listings = pd.DataFrame(thorough_listings)
        geolocated_filtered_listings = geolocated_filtered_listings[pd.notnull(geolocated_filtered_listings['latitude'])]
        geolocated_filtered_listings = geolocated_filtered_listings[pd.notnull(geolocated_filtered_listings['longitude'])]
        cols = ['pid', 'date', 'region', 'neighborhood', 'rent', 'bedrooms', 'sqft', 'rent_sqft', 'bathrooms' 
                'longitude', 'latitude']
        data_output = geolocated_filtered_listings[cols]

        # TO DO: exception handling for fips
        fips = data_output.apply(self._get_fips, axis=1)             
        geocoded = pd.concat([data_output, fips], axis=1)

        # print('{0} geocoded listings'.format(len(geocoded)))
        return geocoded, len(all_listings), len(thorough_listings), len(geocoded)

    def _write_db(self, dataframe, domain):
        dbname = 'craigslist'
        host='localhost'
        port=5432
        username='mgardner'
        passwd='craig'
        conn_str = "dbname={0} user={1} host={2} password={3} port={4}".format(dbname,username,host,passwd,port)
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        num_listings = len(dataframe)
        # print("Inserting {0} listings from {1} into database.".format(num_listings, domain))
        prob_PIDs = []
        dupes = []
        writes = []
        for i,row in dataframe.iterrows():
            try:
                cur.execute('''INSERT INTO rental_listings
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                (row['pid'],row['date'].to_datetime(),row['region'],row['neighborhood'],
                                row['rent'],row['bedrooms'],row['sqft'],row['rent_sqft'],
                                row['longitude'],row['latitude'],row['county'],
                                row['fips_block'],row['state'],row['bathrooms']))
                conn.commit()
                writes.append(row['pid'])
            except Exception, e:
                if 'duplicate key value violates unique' in str(e):
                    dupes.append(row['pid'])
                else:
                    prob_PIDs.append(row['pid'])
                conn.rollback()
                
        cur.close()
        conn.close()
        return prob_PIDs, dupes, writes
    
    def run(self, charity_proxy=True):
    
        colnames = ['pid','dt','url','title','price','neighb','beds','sqft', 'baths',
                        'lat','lng','accuracy','address']
        st_time = time.time()

        # Loop over each regional Craigslist URL
        for i, domain in enumerate(self.domains):

            total_listings = 0
            listing_num = 0
            ts_skipped = 0

            regionName = domain.split('//')[1].split('.craigslist')[0]
            regionIsComplete = False
            search_url = domain
            logging.info('BEGINNING NEW REGION')

            fname = self.out_dir + regionName + '-' \
                + (self.ts if self.fname_ts else '') + '.csv'

            with open(fname, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(colnames)

                while not regionIsComplete:

                    logging.info(search_url)
                    s = requests.Session()

                    if charity_proxy:
                        requests.packages.urllib3.disable_warnings()
                        authenticator = '87783015bbe2d2f900e2f8be352c414a'
                        proxy_str = 'http://' + authenticator + '@' +'workdistribute.charityengine.com:20000'
                        s.proxies = {'http': proxy_str, 'https': proxy_str}
                        s.auth = HTTPProxyAuth(authenticator,'')

                    try:
                        page = s.get(search_url, timeout=30)
                    except requests.exceptions.Timeout:
                        s = requests.Session()
                        if charity_proxy:
                            s.proxies = {'http': proxy_str, 'https': proxy_str}
                            s.auth = HTTPProxyAuth(authenticator,'')
                        try:
                            page = s.get(search_url, timeout=30)    
                        except:
                            regionIsComplete = True
                            logging.info('FAILED TO CONNECT.')

                    try:
                        tree = html.fromstring(page.content)
                    except:
                        regionIsComplete = True
                        logging.info('FAILED TO PARSE HTML.')

                    listings = tree.xpath('//li[@class="result-row"]')

                    ### TO DO: Need better way to check for HTML changes in Craigslist 
                    if len(listings) == 0 and total_listings == 0:
                        logging.info('NO LISTINGS RETRIEVED FOR {0}'.format(str.upper(regionName)))

                    total_listings += len(listings)
                    

                    for item in listings:

                        listing_num += 1
                        try:
                            row = self._parseListing(item)
                            item_ts = dt.strptime(row[1], '%Y-%m-%d %H:%M')
                
                            if (item_ts > self.latest_ts):
                                # Skip this item but continue parsing search results
                                ts_skipped += 1
                                continue

                            if (item_ts < self.earliest_ts):
                                # Break out of loop and move on to the next region
                                if listing_num == 1:
                                    logging.info('NO LISTINGS BEFORE TIMESTAMP CUTOFF AT {0}'.format(str.upper(regionName)))    
                                else:
                                    logging.info('REACHED TIMESTAMP CUTOFF')
                                ts_skipped += 1
                                regionIsComplete = True
                                break 
                    
                            item_url = domain.split('/search')[0] + row[2]
                            row[2] = item_url

                            # Parse listing page to get lat-lng
                            logging.info(item_url)
                            row += self._scrapeLatLng(s, item_url) 
                            writer.writerow(row)

                        except Exception, e:
                            # Skip listing if there are problems parsing it
                            logging.warning("{0}: {1}. Probably no beds/sqft info".format(type(e).__name__, e))
                            continue
                    
                    next = tree.xpath('//a[@title="next page"]/@href')
                    if len(next) > 0:
                        search_url = domain.split('/search')[0] + next[0]
                    else:
                        regionIsComplete = True
                        logging.info('RECEIVED ERROR PAGE')

                    s.close()
            
            # print ts_skipped

            if ts_skipped == total_listings:
                logging.info(('{0} TIMESTAMPS NOT MATCHING' +
                             ' - CL: {1} vs. UAL: {2}.' +
                             ' NO DATA SAVED.').format(
                                 regionName,
                                 str(item_ts),
                                 str(self.latest_ts)))
                continue


            cleaned, count_listings, count_thorough, count_geocoded = self._clean_listings(fname)
            num_cleaned = len(cleaned)

            if num_cleaned > 0:
                probs, dupes, writes = self._write_db(cleaned, domain)
                num_probs = len(probs)
                num_dupes = len(dupes)
                num_writes = len(writes)
                assert num_probs + num_dupes + num_writes == num_cleaned 
                pct_written = (num_writes) / num_cleaned * 100
                pct_fail = round(num_probs / num_cleaned * 100,3)

                if num_dupes == num_cleaned:
                    logging.info('100% OF {0} PIDS ARE DUPES. NOTHING WRITTEN'.format(str.upper(regionName)))

                elif num_writes + num_dupes == num_cleaned:
                    logging.info('100% OF {0} PIDS WRITTEN.'.format(str.upper(regionName)) + 
                                 ' {0} scraped, {1} w/ rent/sqft, {2} w/ lat/lon, {3} dupes'.format(
                                    count_listings, count_thorough, count_geocoded, num_dupes))
                
                else:
                    logging.info('FAILED TO WRITE {0}% OF {1} PIDS:'.format(pct_fail,str.upper(regionName)) + ', '.join(probs))

            else:
                logging.info('NO CLEAN LISTINGS FOR {0}:'.format(str.upper(regionName)) + 
                             ' {0} scraped, {1} w/ rent/sqft, {2} w/ lat/lon.'.format(
                                count_listings, count_thorough, count_geocoded))

        return











