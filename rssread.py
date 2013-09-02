#!/usr/bin/python3

import feedparser
import json
import datetime
import time
import pickle
import copy
import queue
import threading
import os

import socket
socket.setdefaulttimeout(10)

debug = True

max_connections = 15

feeds_list = json.load(open("feeds.json", 'r'))

feeds_file_name = "tmpfeeds.pickle"

entries = []

error_list = []


def error(msg):
    error_list.append(msg)
    if debug:
        print ("ERROR: " + msg)


try:
    with open(feeds_file_name, "rb") as f:
        loaded_feeds = pickle.load(f)
except FileNotFoundError:
    loaded_feeds = {}
except Exception as e:
    error("tmp pickle file reading failed :" + str(e))
    loaded_feeds = {}

url_queue = queue.Queue(max_connections)


def get_rss(feed_descr):
    url = feed_descr['url']
    img = feed_descr.get('img', '')
    wotags = feed_descr.get('wotags', [])
    if debug:
        print ("Reading feeds from {}".format(url))
    prev_feed = loaded_feeds.get(url)

    try:
        if prev_feed:
            #http://packages.python.org/feedparser/http-etag.html#using-etags-to-reduce-bandwidth
            try:
                etag = prev_feed.etag
            except AttributeError:
                if debug:
                    print ("Warning: feed {} has no etag attribute".format(url))
                etag = None
            try:
                modified = prev_feed.modified
            except AttributeError:
                if debug:
                    print ("Warning: feed {} has no modified attribute".format(url))
                modified = None
            feed = feedparser.parse(url, etag=etag, modified=modified)
        else:
            feed = feedparser.parse(url)
        if feed.status == 304:
            if debug:
                print ("Information: feed {} returned a 304 status. Keeping old feed".format(url))
        else:
            feed['img'] = img
            feed['wotags'] = wotags
            loaded_feeds[url] = copy.copy(feed)
            if debug:
                print ("Information: feed {} retrieved".format(url))
    except:
        error("Error while retrieving feed {}".format(url))


def worker():
    while True:
        feed_descr = url_queue.get()
        get_rss(feed_descr)
        url_queue.task_done()

for i_thread in range(max_connections):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

for feed_descr in feeds_list:
    url_queue.put(feed_descr)

url_queue.join()

try:
    f = open(feeds_file_name, "wb")
    pickle.dump(loaded_feeds, f)
except Exception as e:
    os.remove(feeds_file_name)
    error("tmp pickle file write failed: " + str(e))


for (url, feed) in loaded_feeds.items():
    if debug:
        print ("Decoding feeds from {}".format(url))
    for item in feed['items']:
        item['img'] = feed['img']
        if item["updated_parsed"] is None:
            error("date error for entry {} in feed {}".format(item['title'], url))
            item["updated_parsed"] = time.localtime()
        if 'tags' in item:
            taglist = [tag['term'] for tag in item['tags']]
            item['taglist'] = taglist
        else:
            item['taglist'] = []
        #we filter out items with tags in wotags list
        if not set(item['taglist']) & set(feed['wotags']):
            entries.append(item)

sorted_entries = sorted(entries, key=lambda entry: entry["updated_parsed"])
sorted_entries.reverse()

out_file = "index.html"
out = open(out_file, "w")

out.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Suivi des flux RSS</title>
</head>
<style>
a:link {text-decoration:none; color:black}
a:hover {text-decoration:underline}
a:visited {color:grey}
.date { text-align:right; margin-right:200px; font-weight:bold }
.content { max-width:1000px; margin-left:auto; margin-right:auto }
.link { margin-left:16px; text-indent:-16px; line-height:150% }
.link_bloc { }
</style>
<body>
""")

today = datetime.date.today()

for msg in error_list:
    out.write("{}</br></a>\n".format(msg))

out.write("<div class=content>\n")

curr_date = None
for elem in sorted_entries:
    datep = elem['updated_parsed']
    date = datetime.date(datep[0], datep[1], datep[2])
    time = datetime.time(datep[3], datep[4])
    age = today - date
    if age.total_seconds() / (3600 * 24) > 7:
        break
    if date != curr_date:
        if curr_date is not None:
            out.write("</div>\n")  # End of previous link_bloc
        out.write("<div class=date>{}</div>\n".format(date.strftime("%d %B")))
        out.write("<div class=link_bloc>\n")
        curr_date = date
    title_str = ", ".join(elem['taglist'])
    out.write('<div class=link><img src="{}" width=16/> <a href={} title="{}">{}</a></div>\n'.format(elem['img'], elem['link'], title_str, elem['title']))

out.write("</div></div></body></html>")
