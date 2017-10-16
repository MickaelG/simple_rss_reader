#!/usr/bin/python3

import sys

import json
import datetime
import logging
import sqlite3
import argparse

import feedparser
from bottle import template, run, route
import bottle

import socket
socket.setdefaulttimeout(10)


class Feeds:
    def __init__(self):
        self.content = []

    def __len__(self):
        return len(self.content)

    def __getitem__(self, key):
        return self.content[key]

    def __str__(self):
        return "\n".join([str(feed) for feed in self.content])

    def add_feed(self, url, img_url):
        new_feed = Feed(url, img_url)
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
    def __init__(self, url, img_url=None):
        self.url = url
        self.img_url = img_url
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


def date_to_str(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def read_feeds_list(file_handle):
    parsed_feeds = json.load(file_handle)
    feeds = Feeds()
    for feed in parsed_feeds:
        feeds.add_feed(feed["url"], feed.get("img", None))
    return feeds


def generate_index_html(links, errors):
    return template("index", errors=errors, links=links)


def generate_links_list(feeds):
    all_links = feeds.collect_links()
    today = datetime.date.today()

    links = []

    curr_date = None
    date_links = []
    sorted_entries = sorted(all_links, key=lambda entry: entry.timestamp, reverse=True)
    for entry in sorted_entries:
        age = today - entry.date
        if age.total_seconds() / (3600 * 24) > 7:
            break
        if entry.date != curr_date:
            if curr_date is not None:
                links.append({"date": curr_date.strftime("%d %B"), "links": date_links})
            date_links = []
            curr_date = entry.date
        date_links.append(entry)
    links.append({"date": curr_date.strftime("%d %B"), "links": date_links})

    return links


def save_feeds(feeds, db_connection):
    db_connection.execute('DROP TABLE IF EXISTS links')
    db_connection.execute('DROP TABLE IF EXISTS feeds')
    db_connection.execute('CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY, url TEXT, img_url TEXT)')
    db_connection.execute('CREATE TABLE IF NOT EXISTS links (feed_id INTEGER, title TEXT, url TEXT, timestamp TEXT, FOREIGN KEY(feed_id) REFERENCES feeds(id))')
    for ifeed, feed in enumerate(feeds.content):
        db_connection.execute('INSERT INTO feeds VALUES (?, ?, ?)', (ifeed, feed.url, feed.img_url))
        for link in feed.content:
            db_connection.execute('INSERT INTO links VALUES (?, ?, ?, ?)', (ifeed, link.title, link.url, date_to_str(link.timestamp)))
    db_connection.commit()


def get_saved_feeds(db_connection):
    feeds = Feeds()
    feed_cursor = db_connection.cursor()
    for feed_row in feed_cursor.execute('SELECT * FROM feeds'):
        feed = feeds.add_feed(feed_row[1], feed_row[2])
        link_cursor = db_connection.cursor()
        for link_row in link_cursor.execute('SELECT * FROM links WHERE feed_id=?', (feed_row[0],)):
            timestamp = datetime.datetime.strptime(link_row[3], "%Y-%m-%d %H:%M:%S")
            feed.content.append(FeedEntry(feed, link_row[1], link_row[2], timestamp))
    return feeds


@route("/")
def root():
    with sqlite3.connect("cache.db") as db_connection:
        feeds = get_saved_feeds(db_connection)
    links = generate_links_list(feeds)
    errors = []
    return generate_index_html(links, errors)


@route("/update")
def update():
    with open("feeds.json", "r") as f:
        feeds = read_feeds_list(f)
    feeds.parse()
    errors = []
    with sqlite3.connect("cache.db") as db_connection:
        save_feeds(feeds, db_connection)
    links = generate_links_list(feeds)
    return generate_index_html(links, errors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='simple rss read server')
    parser.add_argument("--debug", action='store_true', help='Activate debug mode')
    parser.add_argument("--update", action='store_true', help='Update feeds instead of running the server')
    args = parser.parse_args()

    if args.update:
        logging.getLogger().setLevel(logging.DEBUG)
        update()
        sys.exit(0)

    if args.debug:
        bottle.debug(True)
        logging.getLogger().setLevel(logging.DEBUG)
    run(reloader=args.debug)

