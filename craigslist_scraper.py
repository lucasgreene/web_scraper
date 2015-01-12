import requests
from bs4 import BeautifulSoup as BS
import re
import pandas as pd
from matplotlib import pylab as plt
from time import time

# search query to use
query = '/search/sss?sort=rel&query=Macbook'
# global craigslist site with US listings first
global_link = 'http://www.craigslist.org/about/sites#US'


print 'Requesting global webpage...'
r = requests.get(global_link)
if r.status_code == 200:
    print "Request completed"
else:
    print "Request failed"
    quit()
raw_html = r.text

# Initialize BeautifulSoup object
soup = BS(raw_html, 'html.parser')

# Grab the links to all the US regions by selecting first colmask tag
# and then grabbing all href tags
US_listings = soup.find('div', {'class': 'colmask'})
regions = US_listings.find_all('a')
region_links = [a['href'] for a in regions]
region_names = [a.text for a in regions]
print "Grabbed %s region links" %len(regions)

t0 = time()


prices = []

for link in region_links:

    print "SCRAPING "+ link
    search_link = link+query

    # get webpage and raw html
    print "Requesting webpage " + search_link + ' ...'
    r = requests.get(search_link)
    if r.status_code == 200:
        print "Request completed"
    else:
        print "Request failed"
        quit()

    ad_page_html = r.text

    # create BeautifulSoup object with raw html
    soup = BS(ad_page_html, 'html.parser')

    # Total number of listings, if not listed restrict to one page
    totalcount = soup.find('span', {'class': 'totalcount'})
    if totalcount:
        count = int(totalcount.text)
    else:
        count = 100
    
    # Number of pages not displayed, i.e number of next buttons to follow
    num_pages = (count-1)/100

    # Grab all listings
    rows = soup.find_all('p', {'class': 'row'})

    # Grap a price for each listing, if it exists
    print "grabbing prices..."
    [prices.append(row.a.span.text) for row in rows if row.a.span]

    # Follow the link to the next page, repeat process
    for i in range(num_pages):

        next_link = link + soup.find('a', {'class': 'button next'})['href']
         
        print "requesting webpage " + next_link + " ..."
        r = requests.get(next_link)
        if r.status_code == 200:
           print "Request completed"
        else:
           print "Request failed"
           quit()
        ad_page_html = r.text
        soup = BS(ad_page_html, 'html.parser')
        rows = soup.find_all('p', {'class': 'row'})
        print 'grabbing prices...'
        [prices.append(row.a.span.text) for row in rows if row.a.span]

t1 = time()

print "done scraping all prices"
print "Time elapsed = %f" %(t1-t0)

# Write prices to txt file for later use
with open('prices.txt', 'wb') as File:
    for line in prices:
        File.write(line + '\n')

# Analysis
# Convert prices to floats

price_floats = [float(re.sub('[$]','',p)) for p in prices]

# Create dataframe
df = pd.DataFrame(price_floats, columns = ['prices'])
# Drop outliers. I'm assuming here that anything under 100$ or over $3000 not real
# Also drop any NA
df = df[(df['prices'] > 100) & (df['prices']<3000)].dropna()

#plot the prices in a histogram
plt.hist(df['prices'], bins=40)
plt.show()
