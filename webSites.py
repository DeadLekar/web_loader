from selenium import webdriver
from paths import *
import urllib.request as http
import time
import sqlite3 as sql
import serviceFunctions as sf
import pandas as pd



class Sravni:
    start_link = 'https://www.sravni.ru/novosti/'
    driver = None
    stop_count = ""
    all_links = []
    new_links = []
    conn = None
    c = None

    def __init__(self, _driver, _stop_count, _conn):
        self.driver = _driver
        self.driver.maximize_window()
        self.STOP_COUNT = _stop_count
        self.conn = _conn
        self.c = self.conn.cursor()
        # get known links to avoid double reading
        self.load_all_links_from_db()

    def load_all_links_from_db(self):
        link_rows = self.c.execute("SELECT link FROM links WHERE siteName='Sravni'").fetchall()
        for row in link_rows:
            self.all_links.append(row[0])

    def load_new_links_from_db(self):
        link_rows = self.c.execute("SELECT link FROM links WHERE siteName='Sravni' AND cntViews is Null").fetchall()
        for row in link_rows:
            self.new_links.append(row[0])

    def get_links(self):
        self.driver.get(self.start_link)
        # read links
        article_cards = []
        while len(article_cards) < self.STOP_COUNT:
            article_cards = self.driver.find_elements_by_class_name('article-preview')
            self.load_more()
            time.sleep(2)

        # save links to db
        for card in article_cards:
            link = card.find_element_by_tag_name('a').get_attribute('href')
            if link not in self.all_links:
                self.all_links.append(link)
                self.c.execute("INSERT INTO links (link, siteName) VALUES ('{}','Sravni')".format(link))
        self.conn.commit()

    def read_articles_data(self):
        self.load_new_links_from_db()
        for link in self.new_links:
            self.driver.get(link)
            try:
                title = sf.clear_string(self.driver.find_element_by_class_name('heading-big').text, sf.digits + sf.rus_letters + sf.lat_letters + sf.puncts + " ")
                cnt_views = int(sf.clear_string(self.driver.find_element_by_class_name('views-value').text, sf.digits))
                date_publ = self.driver.find_element_by_class_name('article-info-date').text
                text_len = len(self.driver.find_element_by_class_name('article__main-content').text)
                self.c.execute("UPDATE links SET cntViews={} WHERE link='{}'".format(cnt_views, link))
                self.c.execute("UPDATE links SET title='{}' WHERE link='{}'".format(title, link))
                self.c.execute("UPDATE links SET datePubl='{}' WHERE link='{}'".format(date_publ, link))
                self.c.execute("UPDATE links SET textLen={} WHERE link='{}'".format(text_len, link))
                print("{}: views {}, length {}".format(title, cnt_views, text_len))
                self.conn.commit()
            except: pass
            time.sleep(1)

    def load_more(self):
        btn = self.driver.find_element_by_class_name('anchor-block-text')
        btn.click()

class Banki:
    start_link = ''
    driver = None
    stop_count = 0
    all_links = []
    new_links = []
    conn = None
    c = None

    def __init__(self, _start_link, _driver, _stop_count, _conn):
        self.driver = _driver
        self.start_link = _start_link
        self.driver.maximize_window()
        self.STOP_COUNT = _stop_count
        self.conn = _conn
        self.c = self.conn.cursor()
        # get known links to avoid double reading
        self.load_all_links_from_db()

    def load_all_links_from_db(self):
        link_rows = self.c.execute("SELECT link FROM links WHERE siteName='Banki'").fetchall()
        for row in link_rows:
            self.all_links.append(row[0])

    def load_new_links_from_db(self):
        link_rows = self.c.execute("SELECT link FROM links WHERE siteName='Banki' AND (textLen=0 OR cntViews=0)").fetchall()
        for row in link_rows:
            self.new_links.append(row[0])

    def get_links(self):
        # read links
        self.driver.get(self.start_link)
        cnt_pages = 1
        while cnt_pages <= self.STOP_COUNT:
            page_article_cards = self.driver.find_elements_by_class_name('margin-bottom-default')
            for card in page_article_cards:
                try:
                    link = card.find_element_by_tag_name('a').get_attribute('href')
                    if link not in self.all_links:
                        self.all_links.append(link)
                        self.c.execute("INSERT INTO links (link, siteName) VALUES ('{}','Banki')".format(link))
                except: pass
            self.conn.commit()
            cnt_pages += 1
            self.driver.get(self.get_next_page_link(cnt_pages))
            time.sleep(2)

        # save links to db


    def read_articles_data(self):
        self.load_new_links_from_db()
        for link in self.new_links:
            cnt_views = text_len = 0
            title = date_publ = ''
            self.driver.get(link)
            time.sleep(1)
            try:
                title = sf.clear_string(self.driver.find_element_by_class_name('header-h0').text, sf.digits + sf.rus_letters + sf.lat_letters + sf.puncts + " ")
            except: pass
            article_data = ''
            for xpath in ['/html/body/div[1]/div[1]/div[1]/main/div[1]/span', '/html/body/div[1]/div[1]/div[1]/main/div[2]/span', '/html/body/div[1]/div[1]/div[1]/main/div[1]/div[2]/span']:
                try:
                    article_data = self.driver.find_element_by_xpath(xpath)
                except: pass
                if article_data: break
            if article_data:
                data_arr = article_data.text.split(" ")
                date_publ = data_arr[0]
                cnt_views = data_arr[2]
            try:
                text_len = len(self.driver.find_element_by_class_name('article-text').text)
            except: pass

            self.c.execute("UPDATE links SET cntViews={} WHERE link='{}'".format(cnt_views, link))
            self.c.execute("UPDATE links SET title='{}' WHERE link='{}'".format(title, link))
            self.c.execute("UPDATE links SET datePubl='{}' WHERE link='{}'".format(date_publ, link))
            self.c.execute("UPDATE links SET textLen={} WHERE link='{}'".format(text_len, link))
            print("{}: views {}, length {}".format(title, cnt_views, text_len))
            self.conn.commit()

    def get_next_page_link(self, next_page_num):
        link_arr = self.driver.current_url.split('=')
        return link_arr[0] + '=' + str(next_page_num)


db_name = get_right_path(db_paths) + 'finsites.db'
conn = sql.connect(db_name)

chrome_path = get_right_path(driver_paths)
driver = webdriver.Chrome(chrome_path)

# sravni = Sravni(driver, 500, conn)
# sravni.get_links()
# sravni.read_articles_data()
# banki = Banki('https://www.banki.ru/news/daytheme/?page=1', driver, 35, conn)
# banki.get_links()
# banki = Banki('https://www.banki.ru/news/columnists/?page=1', driver, 25, conn)
# banki.get_links()
banki = Banki('', driver, 25, conn)
banki.read_articles_data()
