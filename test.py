#!/usr/bin/python3

import unittest
import datetime
import sqlite3

import io

from rssread2 import Feed, FeedEntry, read_feeds_list
import rssread2

class TestFeed(unittest.TestCase):
    def test_parse(self):
        feeds_json = io.StringIO('[{"url":"url1", "img":"img1"}, {"url":"url2", "img":"img2"}]')
        feeds = read_feeds_list(feeds_json)
        self.assertEqual(len(feeds), 2)
        self.assertEqual(feeds[0].url, "url1")
        self.assertEqual(feeds[0].img_url, "img1")
        self.assertEqual(feeds[1].url, "url2")
        self.assertEqual(feeds[1].img_url, "img2")

    def test_parse_feeds(self):
        feeds_json = io.StringIO('[{"url":"url1"}]')
        feeds = read_feeds_list(feeds_json)
        self.assertEqual(len(feeds), 1)
        self.assertEqual(feeds[0].url, "url1")
        self.assertEqual(feeds[0].img_url, None)


    def test_parse(self):
        raw_feed = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Liens</title>
<updated>2017-09-30T20:21:03+04:00</updated>
<entry><title>art1</title><link href="http://test.com/art1"/><updated>2017-09-30T19:21:03+04:00</updated></entry>
<entry><title>art2</title><link href="http://test.com/art2"/><updated>2017-09-30T19:21:03+04:00</updated></entry>'
</feed>"""
        feed = Feed(raw_feed)
        feed.parse()
        self.assertEqual(len(feed.content), 2)
        self.assertEqual(feed.content[0].title, "art1")
        self.assertEqual(feed.content[0].url, "http://test.com/art1")
        self.assertEqual(str(feed.content[0].timestamp), "2017-09-30 15:21:00")
        self.assertEqual(str(feed.content[0].date), "2017-09-30")


class TestTpl(unittest.TestCase):
    def test_basic(self):
        dummy_timestamp = datetime.datetime.now()
        links = []
        parent_feed = Feed(None, "my_img_url")
        date_links = []
        date_links.append(FeedEntry(parent_feed, "title1", "url1", dummy_timestamp))
        date_links.append(FeedEntry(parent_feed, "title2", "url2", dummy_timestamp))
        links.append({"date": "04 Octobre", "links": date_links})
        date_links = []
        date_links.append(FeedEntry(parent_feed, "title3", "url3", dummy_timestamp))
        links.append({"date": "03 Octobre", "links": date_links})
        errors = ["No errors"]
        result = rssread2.generate_index_html(links, errors)


class TestDB(unittest.TestCase):
    def test_basic(self):
        dummy_date = datetime.datetime.now()
        feeds = rssread2.Feeds()
        feed1 = feeds.add_feed("feed_url1", "feed_img1")
        feed2 = feeds.add_feed("feed_url2", "feed_img2")
        feed1.content.append(FeedEntry(feed1, "f1_title", "f1_link", dummy_date))
        feed1.content.append(FeedEntry(feed1, "f2_title", "f2_link", dummy_date))
        feed2.content.append(FeedEntry(feed2, "f3_title", "f3_link", dummy_date))
        db_connection = sqlite3.connect(":memory:")
        rssread2.save_feeds(feeds, db_connection)
        loaded_feeds = rssread2.get_saved_feeds(db_connection)
        self.assertEqual(str(loaded_feeds), str(feeds))


if __name__ == "__main__":
    unittest.main()

