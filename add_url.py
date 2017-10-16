#!/usr/bin/python3

import sys
import lxml.html
from urllib.request import urlopen
from urllib.error import HTTPError


url = sys.argv[1]

doc = lxml.html.parse(url)
rss_list = doc.xpath('//link[@type="application/rss+xml"]/@href')
atom_list = doc.xpath('//link[@type="application/atom+xml"]/@href')
feeds_list = rss_list + atom_list
if len(feeds_list) > 0:
    feed = feeds_list[0]
if len(feeds_list) > 1:
    print("Warning: More than one feed found: %s" % str(feeds_list))
print("feed: %s" % str(feed))

#favicon_list = doc.xpath('//link[@type="image/ico"]/@href')
favicon_list = doc.xpath('//link[@rel="icon"]/@href')
favicon_list.extend(doc.xpath('//link[@rel="shortcut icon"]/@href'))
if len(favicon_list) == 0:
    print("No favicon found in html, trying default")
    favicon = "%s/favicon.ico" % url
    try:
        urlopen(favicon)
    except HTTPError:
        print("Default favicon does not exist")
        favicon = None
else:
    favicon = favicon_list[0]
print("favicon: %s" % str(favicon))

result = '{"url":"%s"' % feed
if favicon:
    result += ', "img":"%s"' % favicon
result += '},'

print(result)
