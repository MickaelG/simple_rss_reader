#!/usr/bin/python3

import bottle
import os, datetime

app = bottle.Bottle()

@app.route('/')
def root():
	#We regenerate index.html only if last generation is more than 1 hour old
	last_mod = datetime.datetime.fromtimestamp(os.path.getmtime("index.html"))
	now = datetime.datetime.now()
	if ( now - last_mod ).total_seconds() > 60*60:
		os.system("python3 rssread.py")
	return bottle.static_file("index.html", root=".")

@app.route('/update')
def update():
	os.system("python3 rssread.py")
	return bottle.static_file("index.html", root=".")

bottle.run(app, host='localhost', port=8080)

