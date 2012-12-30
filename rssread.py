#!/usr/bin/python3

import feedparser, json, datetime

feeds_list = json.load(open("feeds.json",'r'))

entries=[]

#http://packages.python.org/feedparser/http-etag.html#using-etags-to-reduce-bandwidth
for (url,img) in feeds_list:
	feed=feedparser.parse(url)
	for item in feed['items']:
		item['img']=img
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
