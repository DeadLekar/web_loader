from selenium import webdriver
from bs4 import BeautifulSoup
import lxml.html as html
from paths import *
import urllib.request as http
import time
import serviceFunctions as sf
import sqlite3 as sql

class Sravni:
    start_link = 'https://www.sravni.ru/novosti/'
    driver = None
    stop_date = ""

    def __init__(self, _driver, _stop_date):
        self.driver = _driver
        self.driver.maximize_window()
        self.stop_date = _stop_date

    def load_pages(self):
        self.driver.get(self.start_link)

        pass




chrome_path = get_right_path(driver_paths)
driver = webdriver.Chrome(chrome_path)
sravni = Sravni(driver, "01.01.2020")
sravni.load_pages()