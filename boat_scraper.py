import requests
from bs4 import BeautifulSoup as BS
import re
import csv
import sqlite3 as lite
import time
import random


global_link = 'http://www.boattrader.com'


def throttle(t=0.25):
    # Sleep the operation for a set time.
    time.sleep(random.random() * t)

def get_soup_object(link):
    """ Takes as input a valid link and returns the
    BeautifulSoup object that parses the HTML of the page
    """
    print link
    r = requests.get(link)
    if r.status_code != 200:
        print "request failed for " + link
        quit()
    html = r.text
    return BS(html, 'html.parser')

def get_info(local_link):
    """ Takes a local link (not valid) and then parses the HTML
    for a single boat listing of make,model,contact, and price.
    Returns a list of these values
    """
    link = global_link + local_link
    soup = get_soup_object(link)
    info = soup.find('header', {'class': 'bd-header'})
    make = info.find('span', {'class': 'bd-make'}).text
    model = info.find('span', {'class': 'bd-model'}).text
    price = info.find('span', {'class': 'bd-price'}).text.strip()
    contact = soup.find('div', {'class': 'phone'}).text[::-1]
    contact = re.sub('[)(]', '', contact)     # Remove parenthesis
    return [make, model, contact, price]

def main(csv_writer, db_cursor, n):
    """ Uses the search_link as a starting page, scrapes info from all 25
    listings on this page before repeating the process on the next page
    of 25 listings. Stops when the number of visited listings = 800.
    It will skip any listings that have invalid html for the built-in 
    html parser. Takes an open file object and an open connect object, will 
    write every n iterations """   
    search_link = 'http://www.boattrader.com/search-results/NewOrUsed-any/Type-all/Zip-02842/Radius-4000/Sort-Length:DESC'
    print "requesting search page..."
    soup = get_soup_object(search_link)
    print "request completed"
    print "scraping boat info"

    boat_info = []
    count = 0
    failures = 0
    while count < 50:       
        listings = soup.find_all('div', {'class': 'ad-title'})
        links = [post.a['href'] for post in listings]
        for l in links:      # So the program wont crash when given a bad link
            try:
                boat_info.append(get_info(l))
            except:
                failures += 1
        next_link = global_link + soup.find('a', {'title': 'Next Page'})['href']
        count += 25
        print "SCRAPED %s PAGES..." % count
        print "%s FAILURES" % failures
        soup = get_soup_object(next_link)
        throttle()
        if count % n == 0:
            # Write to db
            db_cursor.executemany("INSERT INTO Boats VALUES(?, ?, ?, ?)", boat_info)
            # Write to csv
            for line in boat_info:
                csv_writer.writerow(line)
            boat_info = []

        File.close()
        con.commit()
        con.close()


if __name__ == '__main__':
    File = open('boat_info.txt', 'wb')     # Create the open file and
    con = lite.connect('leada.db')         # sqlite3 connection objects
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS Boats")
    cur.execute("CREATE TABLE Boats(Make TEXT, Model TEXT, Contact TEXT, Price TEXT)")
    writer = csv.writer(File)
    try:
        main(writer, cur, n = 25)
    except Exception as e:
        File.close()
        con.commit()
        con.close()
        print e




