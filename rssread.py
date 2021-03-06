#!/usr/bin/python3

import sys

import json
import datetime
import sqlite3
import argparse
import urllib.request

import logging
logging.getLogger().setLevel(logging.DEBUG)

import feedparser
import flask
app = flask.Flask(__name__)

import socket
socket.setdefaulttimeout(10)

import bs4


class Feeds:
    def __init__(self):
        self.content = []

    def __len__(self):
        return len(self.content)

    def __getitem__(self, key):
        return self.content[key]

    def __str__(self):
        return "\n".join([str(feed) for feed in self.content])

    def add_feed(self, url, img_url, type):
        new_feed = Feed(url, img_url, type)
        self.content.append(new_feed)
        return new_feed

    def parse(self):
        for feed in self.content:
            feed.parse()

    def collect_links(self):
        result = []
        for feed in self.content:
            for entry in feed.content:
                result.append(entry)
        return result


class Feed:
    def __init__(self, url, img_url=None, type=None):
        self.url = url
        self.img_url = img_url
        self.type = type
        self.content = []

    def __str__(self):
        head_str = self.url + " (" + self.img_url + ")"
        return head_str + "\n" + "\n".join(["  " + str(entry) for entry in self.content])

    def parse(self):
        logging.debug("Parsing feed " + self.url)
        parsed_feed = feedparser.parse(self.url)
        for item in parsed_feed['items']:
            link = item['link']
            title = item['title']
            datep = item['updated_parsed']
            date = datetime.datetime(datep[0], datep[1], datep[2],
                                     datep[3], datep[4])
            self.content.append(FeedEntry(self, title, link, date, None))


class FeedEntry:
    def __init__(self, parent_feed, title, url, timestamp, tags=None):
        self.parent_feed = parent_feed
        self.title = title
        self.url = url
        assert(isinstance(timestamp, datetime.datetime)), timestamp
        self.timestamp = timestamp
        self.tags = tags

    def __str__(self):
        return self.title + ": " + self.url + " (" + date_to_str(self.timestamp) + ")"

    @property
    def img_url(self):
        return self.parent_feed.img_url

    @property
    def date(self):
        return self.timestamp.date()

    @property
    def type(self):
        return self.parent_feed.type


def date_to_str(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def read_feeds_list(file_handle):
    parsed_feeds = json.load(file_handle)
    feeds = Feeds()
    for feed in parsed_feeds:
        feeds.add_feed(feed["url"], feed.get("img", None), feed.get("type", ""))
    return feeds


def generate_links_list(feeds):
    all_links = feeds.collect_links()
    today = datetime.date.today()

    links = []

    curr_date = None
    date_links = []
    sorted_entries = sorted(all_links, key=lambda entry: entry.timestamp, reverse=True)
    for entry in sorted_entries:
        assert(entry.date is not None)
        age = today - entry.date
        if age.total_seconds() / (3600 * 24) > 7:
            break
        if entry.date != curr_date:
            if curr_date is not None:
                links.append({"date": curr_date.strftime("%d %B"), "links": date_links})
            date_links = []
            curr_date = entry.date
        date_links.append(entry)
    if date_links:
        links.append({"date": curr_date.strftime("%d %B"), "links": date_links})

    return links


def save_feeds(feeds, db_connection):
    db_connection.execute('DROP TABLE IF EXISTS links')
    db_connection.execute('DROP TABLE IF EXISTS feeds')
    db_connection.execute('CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY, url TEXT, img_url TEXT, type TEXT)')
    db_connection.execute('CREATE TABLE IF NOT EXISTS links (feed_id INTEGER, title TEXT, url TEXT, timestamp TEXT, FOREIGN KEY(feed_id) REFERENCES feeds(id))')
    for ifeed, feed in enumerate(feeds.content):
        db_connection.execute('INSERT INTO feeds VALUES (?, ?, ?, ?)', (ifeed, feed.url, feed.img_url, feed.type))
        for link in feed.content:
            db_connection.execute('INSERT INTO links VALUES (?, ?, ?, ?)', (ifeed, link.title, link.url, date_to_str(link.timestamp)))
    db_connection.commit()


def get_saved_feeds(db_connection, type):
    feeds = Feeds()
    feed_cursor = db_connection.cursor()
    for feed_row in feed_cursor.execute('SELECT * FROM feeds WHERE type=?', (type,)):
        feed = feeds.add_feed(feed_row[1], feed_row[2], feed_row[3])
        link_cursor = db_connection.cursor()
        for link_row in link_cursor.execute('SELECT * FROM links WHERE feed_id=?', (feed_row[0],)):
            timestamp = datetime.datetime.strptime(link_row[3], "%Y-%m-%d %H:%M:%S")
            feed.content.append(FeedEntry(feed, link_row[1], link_row[2], timestamp))
    return feeds


@app.route("/")
def root():
    with sqlite3.connect("cache.db") as db_connection:
        feeds = get_saved_feeds(db_connection, "")
    links = generate_links_list(feeds)
    errors = []
    return flask.render_template("index.html", errors=errors, links=links)

@app.route("/actu")
def actu():
    with sqlite3.connect("cache.db") as db_connection:
        feeds = get_saved_feeds(db_connection, "actu")
    links = generate_links_list(feeds)
    errors = []
    return flask.render_template("index.html", errors=errors, links=links)

@app.route("/feeds")
def feeds():
    with open("feeds.json", "r") as f:
        feeds = read_feeds_list(f)
    return flask.render_template("feeds.html", feeds=feeds)


@app.route("/update")
def update():
    update_feeds()
    return flask.redirect("/")


def update_feeds():
    with open("feeds.json", "r") as f:
        feeds = read_feeds_list(f)
    feeds.parse()
    errors = []
    with sqlite3.connect("cache.db") as db_connection:
        save_feeds(feeds, db_connection)


#@app.route("/favicon/<base_url:path>")
def get_feed_details(base_url):
    req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    soup = bs4.BeautifulSoup(html, "html.parser")

    favicon = get_favicon(soup, base_url)
    rss = get_rss(soup)

    return (rss, favicon)


def get_rss(soup):
    rss_link = soup.find("link", type="application/rss+xml")
    if rss_link is not None:
        return rss_link["href"]
    atom_link = soup.find("link", type="application/atom+xml")
    if atom_link is not None:
        return atom_link["href"]
    return None


def get_favicon(soup, base_url):
    icon_link = soup.find("link", rel="shortcut icon")
    if icon_link is None:
        icon_link = soup.find("link", rel="icon")
    if icon_link is None:
        logging.debug("No favicon found in html of " + base_url + ", trying default")
        favicon = "%s/favicon.ico" % base_url
        try:
            urllib.request.urlopen(favicon)
        except HTTPError:
            logging.debug("Default favicon does not exist")
            favicon = None
    else:
        favicon = icon_link['href']
    if favicon.startswith('/'):
        favicon = base_url + favicon
    return favicon


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='simple rss read server')
    parser.add_argument("--update", action='store_true', help='Update feeds instead of running the server')
    parser.add_argument("--parse_url", help='Get feed and favicon of given URL')
    args = parser.parse_args()

    if args.update:
        update_feeds()
        sys.exit(0)
    if args.parse_url:
        (rss, favicon) = get_feed_details(args.parse_url)
        print('{{"url": "{url}", "img":"{icon}"}}'.format(url=rss, icon=favicon))

