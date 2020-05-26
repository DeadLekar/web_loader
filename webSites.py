from selenium import webdriver
from paths import *
import urllib.request as http
import requests
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
    all_links = []
    new_links = []
    conn = None
    c = None

    def __init__(self, _start_link='', _driver=None, _conn=None):
        self.start_link = _start_link
        if _driver:
            self.driver = _driver
            self.driver.maximize_window()
        if _conn:
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

    def get_links(self, stop_count):
        # read links
        self.driver.get(self.start_link)
        cnt_pages = 1
        while cnt_pages <= stop_count:
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

    def _get_next_page_news(self, url, next_page_num):
        num_pos_start = url.find('page') + 4
        return url[0:num_pos_start] + str(next_page_num) + '/'

    def _split_page_with_dates(self, txt):
        WIDGET_DATE_STR = 'widget__date'
        PAGINATION = 'news-pagination'
        txt = txt[:txt.find(PAGINATION)]
        txt_arr = txt.split(WIDGET_DATE_STR)
        txt_dict = {}
        for el in txt_arr[1:]:
            cr_date_start = el.find('<time>') + 6
            cr_date = el[cr_date_start:cr_date_start + 10]
            txt_dict[cr_date] = el
        return txt_dict

    def _split_news_lines(self, key, val):
        news_arr = val.split('<li>')
        ret_arr = []
        for news_item in news_arr:
            if 'href' in news_item:
                time_publ_start = news_item.find('date') + 6
                time_publ_end = news_item.find('</span', time_publ_start)
                time_publ = news_item[time_publ_start:time_publ_end]
                link_start = news_item.find('href=')+6
                link_end = news_item.find('"', link_start)
                link = 'https://www.banki.ru' + news_item[link_start:link_end]
                title_start = news_item.find('<span>', link_end) + 6
                title_end = news_item.find('</span>', title_start)
                title = str.strip(news_item[title_start:title_end])
                print('{};{};{};{};'.format(key, time_publ, link, title))
        return ret_arr

    def read_news_lines(self, stop_data):
        url = self.start_link
        cnt_pages = 1
        while 1:
            response = requests.get(url)
            if stop_data in response.text: break
            d = self._split_page_with_dates(response.text)
            for key, val in d.items():
                self._split_news_lines(key, val)
            cnt_pages += 1
            url = self._get_next_page_news(url, cnt_pages)


if __name__ == '__main__':
    db_name = get_right_path(db_paths) + 'finsites.db'
    conn = sql.connect(db_name)

    chrome_path = get_right_path(driver_paths)
    # driver = webdriver.Chrome(chrome_path)

    # sravni = Sravni(driver, 500, conn)
    # sravni.get_links()
    # sravni.read_articles_data()
    # banki = Banki('https://www.banki.ru/news/daytheme/?page=1', driver, conn)
    # banki.get_links(35)
    # banki = Banki('https://www.banki.ru/news/columnists/?page=1', driver, conn)
    # banki.get_links(25)
    # banki = Banki(_driver=driver)
    # banki.read_articles_data()
    banki = Banki(_start_link='https://www.banki.ru/news/lenta/page1/')
    banki.read_news_lines('04.2020')

