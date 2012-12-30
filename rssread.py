#!/usr/bin/python3

import feedparser, json, datetime, pickle, copy

feeds_list = json.load(open("feeds.json",'r'))

feeds_file_name = "tmpfeeds.pickle"

entries=[]

try:
	with open(feeds_file_name, "rb") as f:
		loaded_feeds = pickle.load(f)
except FileNotFoundError:
	loaded_feeds = {}

for (url,img) in feeds_list:
	print ("Reading feeds from {}".format(url))
	try:
		prev_feed = loaded_feeds[url]
	except KeyError:
		prev_feed = None
	if prev_feed:
		#http://packages.python.org/feedparser/http-etag.html#using-etags-to-reduce-bandwidth
		try:
			etag = prev_feed.etag
		except AttributeError:
			print ("Warning: feed {} has no etag attribute".format(url))
			etag = None
		try:
			modified = prev_feed.modified
		except AttributeError:
			print ("Warning: feed {} has no modified attribute".format(url))
			modified = None
		feed = feedparser.parse(url, etag=etag, modified=modified)
	else:
		feed = feedparser.parse(url)
	if feed.status == 304:
		print ("Information: feed {} returned a 304 status. Keeping old feed".format(url))
	else:
		feed['img'] = img
		loaded_feeds[url] = copy.copy(feed)

with open(feeds_file_name, "wb") as f:
	pickle.dump(loaded_feeds, f)

for (url, feed) in loaded_feeds.items():
	print ("Decoding feeds from {}".format(url))
	for item in feed['items']:
		item['img']=feed['img']
	entries.extend( feed['items'] )

sorted_entries=sorted(entries, key=lambda entry: entry["updated_parsed"])
sorted_entries.reverse()

out_file = "index.html"
out=open(out_file, "w")

out.write( """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Suivi des flux RSS</title>
</head>
<body>
""")

today = datetime.datetime.now()

for elem in sorted_entries:
	datep = elem['updated_parsed']
	date = datetime.datetime(datep[0], datep[1], datep[2], datep[3], datep[4])
	age = today-date
	if age.total_seconds() > 7*24*60*60:
		break
	out.write( '{} <img src="{}" width=16/><a href={}>{}</a><br/>'.format(date.strftime("%d %b - %Hh%M"), elem['img'], elem['link'], elem['title']) )

out.write( "</body></html>")
