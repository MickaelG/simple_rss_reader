#!/usr/bin/python3

import bottle
import os

app = bottle.Bottle()

@app.route('/')
def show():
	return bottle.static_file("index.html", root=".")

@app.route('/update')
def update():
	os.system("python3 rssread.py")
	return bottle.static_file("index.html", root=".")

bottle.run(app, host='localhost', port=8080)

