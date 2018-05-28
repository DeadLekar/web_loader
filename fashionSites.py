from selenium import webdriver
from bs4 import BeautifulSoup
import lxml.html as html
import urllib.request as http
import time
import serviceFunctions as sf
import sqlite3 as sql


class WebSite:
    visited_links = []
    driver = None
    Card = None
    site_id = -1
    cat = ''
    cards_html_classes = []
    next_page_xpath = ''

    def __init__(self, url, driver, site_id, cat, card, cards_html_classes, next_page_class, cr_conn):
        self.driver = driver
        self.driver.maximize_window()
        self.driver.get(url)
        self.site_id = site_id
        self.cat = cat
        self.Card = card
        self.cards_html_classes = cards_html_classes
        self.next_page_class = next_page_class
        self.cr_conn = cr_conn
        self.cards = []

    def get_all_cards(self):
        """
        reads all cards from self.url
        :return: cards from all pages starting from self.url
        """
        self.get_cards_single()
        while self.load_next_page():
            self.get_cards_single()

    def get_cards_single(self):
        """
        :return: cards from a single web page loaded in self.driver
        """

        # get cards from the page
        items = None
        page = self.driver.execute_script('return document.body.innerHTML')
        soup = BeautifulSoup(''.join(page), 'html.parser')
        for data_set in self.cards_html_classes:
            items = soup.find_all(data_set['type'], data_set['class_name'])
            if items: break
        if not items:
            print('Unable to find cards on {}'.format(self.driver.current_url))
        else:
            for item in items:
                self.cards.append(self.Card.get_data(item, self.driver.current_url))

    def load_next_page(self):
        time.sleep(1)
        txt = self.driver.execute_script('return document.body.innerHTML')
        page = html.document_fromstring(txt)
        el = page.find_class(self.next_page_class)

        if not el:
            print('No next page 1: {}'.format(self.driver.current_url))
            return 0
        xpath = self._get_xpath(el[0])

        MAX_CLICK_ATTEMPTS = 3
        time.sleep(2)
        self.visited_links.append(self.driver.current_url)
        arrow = None
        cnt_attempts = 0
        while 1:
            try:
                arrow = self.driver.find_element_by_xpath(xpath)
            except: pass

            if not arrow:
                if len(self.visited_links) == 0:
                    raise ValueError('Unable to find pagination arrow at {}'.format(self.driver.current_url))
                else:
                    print('No next page 2: {}'.format(self.driver.current_url))
                    return 0
            cnt_attempts += 1
            try:
                x = arrow.location_once_scrolled_into_view
                try:
                    self.driver.execute_script("window.scrollBy(0,50)")
                except: pass
                time.sleep(1)
                arrow.click()
                if self.driver.current_url not in self.visited_links:
                    return 1
            except:
                if self.driver.current_url not in self.visited_links:
                    return 1 # kupivip: the page uploaded when reaching the end of the page
                self.driver.get(self.driver.current_url)
                print('Attempt {}: {}'.format(cnt_attempts,self.driver.current_url))
            if cnt_attempts > MAX_CLICK_ATTEMPTS: break
        print('No next page 3: {}'.format(self.driver.current_url))
        return 0

    def save_cards(self):
        if len(self.cards) > 0:
            # save data
            for card in self.cards:
                cmd = sf.get_insert_command(card, 'prodData')
                sf.execute_query(self.cr_conn, cmd, 3)
            self.cr_conn.commit()

    def make_test(self):
        FIELDS_CNT = 8  # max fields' number in the card
        self.get_cards_single()
        len_sum = 0
        if self.cards:
            for c in self.cards:
                len_sum += len(c)
            print('Mid fullness for {} is {}%'.format(self.site_id, round((len_sum / len(self.cards) / FIELDS_CNT) * 100), 1))
        else:
            print('No cards for {}'.format(self.site_id))
        print('Loading next page...')
        if self.load_next_page(): print('Success')

    def _get_xpath(self, el):
        """
        :param el: lxml node
        :return: xpath for el
        """
        xpath_arr = []
        parent = el.getparent()
        while parent is not None:
            cnt_children = 0 # count of children with the same name
            el_num = 1 # element's number among the same children
            suffix = ''
            # find element's number among the same children
            for child in parent.getchildren():
                if hasattr(child, 'tag') and child.tag == el.tag:
                    cnt_children += 1
                if child is el:
                    el_num = cnt_children
                    if cnt_children > 1: break

            if cnt_children > 1:
                suffix = '[{}]'.format(str(el_num))
            xpath_arr.append(el.tag + suffix)

            # level up
            el = el.getparent()
            parent = el.getparent()

        xpath_arr.append('html')
        xpath_arr.reverse()
        return '/'.join(xpath_arr)


class Card:
    def __init__(self, site_id, cat, cat_id):
        self.webSiteID = site_id
        self.categoryName = cat
        self.categoryNameId = cat_id

    def get_data(self, soup, url):
        pass

    def _get_field_value(self, soup, classes, field_name, url):
        right_items = []
        for data_set in classes:
            items = soup.find_all(data_set['type'], data_set['class_name'])
            if items:
                # select the right items (for items with several class names)
                if data_set.get('attrs'):
                    for item in items:
                        if hasattr(item,'attrs') and item.attrs.get('class'):
                            for attr in data_set['attrs']:
                                if attr in item.attrs['class']:
                                    right_items.append(item)
                                    break
                else:
                    right_items = items

        if not right_items:
            print ('Unable to find {} for {}'.format(field_name,url))
            return False
        if len(right_items) > 1:
            texts = []
            for item in right_items:
                if hasattr(item,'text'):
                    texts.append(item.text)
            return ','.join(texts)
        if not hasattr(right_items[0],'text'):
            print('Unable to find text value {} for {}'.format(field_name,url))
            return False

        return right_items[0].text


class Wildberries(Card):
    def get_data(self, soup, url):
        # brand
        data_dict = {}

        html_classes = [{'class_name':'brand-name','type':'strong'}]
        brandName = sf.clear_string(self._get_field_value(soup, html_classes,'brand', url),sf.rus_letters+sf.lat_letters+sf.digits+sf.puncts+' ')
        if brandName: data_dict['brandName'] = brandName

        # good type
        html_classes = [{'class_name':'goods-name','type':'span'}]
        prodType = self._get_field_value(soup,html_classes,'good type', url)
        if prodType: data_dict['prodType'] = sf.clear_string(prodType, sf.rus_letters + sf.lat_letters + sf.puncts + sf.digits + ' ')

        # full price and disc price
        items = soup.find_all('span', 'price')
        if not items:
            raise ValueError('Unable to find price for {}'.format(url))
        for item in items[0].contents:
            if hasattr(item,'text'):
                price = sf.clear_string(item.text,sf.digits)
                if price:
                    price = int(price)
                    if item.name == 'del':
                        data_dict['fullPrice'] = price
                    elif item.name == 'ins':
                        data_dict['discPrice'] = price
                    else:
                        if not data_dict.get('fullPrice'):
                            data_dict['fullPrice'] = price

        # prod link
        prodLink = soup.find('a','ref_goods_n_p')
        if not prodLink:
            raise ValueError('Unable find prod link for {}'.format(url))
        else:
            data_dict['prodLink'] = prodLink.attrs['href']

        # load date
        data_dict['loadDate'] = time.strftime('%d.%m.%Y', time.localtime())
        data_dict['webSiteID'] = self.webSiteID
        data_dict['categoryName'] = self.categoryName
        data_dict['categoryNameID'] = self.categoryNameId
        return data_dict


class Lamoda(Card):
    def get_data(self, soup, url):
        # brand
        data_dict = {}
        html_classes = [{'class_name': 'products-list-item__brand', 'type': 'div'}]
        brandName = sf.clear_string(self._get_field_value(soup, html_classes, 'brand',url), sf.rus_letters + sf.lat_letters + sf.digits + sf.puncts + ' ')
        if brandName: data_dict['brandName'] = brandName

        # good type
        html_classes = [{'class_name': 'products-list-item__type', 'type': 'span'}]
        prodType = self._get_field_value(soup, html_classes, 'good type',url)
        if prodType: data_dict['prodType'] = sf.clear_string(prodType, sf.rus_letters + sf.lat_letters + sf.puncts + sf.digits + ' ')

        # full price and disc price
        price_soup = soup.find('span', 'price')
        if not price_soup:
            # raise Warning('Unable to find price for {}'.format(url))
            print(('Unable to find price for {}'.format(url)))
        else:
            old_price_soup = price_soup.find('span','price__old')
            if old_price_soup:
                data_dict['fullPrice'] = int(sf.clear_string(old_price_soup.text, sf.digits))
                new_price_soup = price_soup.find('span','price__new')
                if new_price_soup:
                    data_dict['discPrice'] = int(sf.clear_string(new_price_soup.text, sf.digits))
            else:
                data_dict['fullPrice'] = int(sf.clear_string(price_soup.text, sf.digits))


        # prod link
        prodLink = soup.find('a', 'products-list-item__link')
        if not prodLink:
            print('Unable find prod link for {}'.format(url))
        else:
            data_dict['prodLink'] = prodLink.attrs['href']

        # load date
        data_dict['loadDate'] = time.strftime('%d.%m.%Y', time.localtime())
        data_dict['webSiteID'] = self.webSiteID
        data_dict['categoryName'] = self.categoryName
        data_dict['categoryNameID'] = self.categoryNameId
        return data_dict


class Kupivip(Card):
    def get_data(self, soup, url):
        # brand
        data_dict = {}
        html_classes = [{'class_name': 'brand', 'type': 'div'}]
        brandName = sf.clear_string(self._get_field_value(soup, html_classes, 'brand', url), sf.rus_letters + sf.lat_letters + sf.digits + sf.puncts + ' ')
        if brandName: data_dict['brandName'] = brandName

        # good type
        html_classes = [{'class_name': 'name', 'type': 'div'}]
        prodType = self._get_field_value(soup, html_classes, 'good type', url)
        if prodType: data_dict['prodType'] = sf.clear_string(prodType, sf.rus_letters + sf.lat_letters + sf.puncts + sf.digits + ' ')

        # full price and disc price
        price_soup = soup.find('div', 'price')
        if not price_soup:
            # raise Warning('Unable to find price for {}'.format(url))
            print(('Unable to find price for {}'.format(url)))
        else:
            new_price = price_soup.contents[0].text
            data_dict['discPrice'] = int(sf.clear_string(new_price, sf.digits))
            if len(price_soup.contents) > 1:
                old_price = price_soup.contents[1].attrs['data-text']
                data_dict['fullPrice'] = int(sf.clear_string(old_price, sf.digits))

        # prod link
        prodLink = soup.find('a', 'details')
        if not prodLink:
            print('Unable find prod link for {}'.format(url))
        else:
            data_dict['prodLink'] = prodLink.attrs['href']

        # load date
        data_dict['loadDate'] = time.strftime('%d.%m.%Y', time.localtime())
        data_dict['webSiteID'] = self.webSiteID
        data_dict['categoryName'] = self.categoryName
        data_dict['categoryNameID'] = self.categoryNameId
        return data_dict


class Bonprix(Card):
    def get_data(self, soup, url):
        # brand
        data_dict = {}
        html_classes = [{'class_name': 'product-brand', 'type': 'span'}]
        brandName = sf.clear_string(self._get_field_value(soup, html_classes, 'brand', url), sf.rus_letters + sf.lat_letters + sf.digits + sf.puncts + ' ')
        if brandName: data_dict['brandName'] = brandName

        # good type
        html_classes = [{'class_name': 'product-title', 'type': 'span'}]
        prodType = self._get_field_value(soup, html_classes, 'good type', url)
        if prodType: data_dict['prodType'] = sf.clear_string(prodType, sf.rus_letters + sf.lat_letters + sf.puncts + sf.digits + ' ')

        # full price and disc price
        html_classes = [{'class_name':'price-tag', 'type':'span'}]
        price = self._get_field_value(soup, html_classes, 'good price', url)
        data_dict['fullPrice'] = int(sf.clear_string(price, sf.digits))

        # prod link
        prodLink = soup.find('a', 'product-link')
        if not prodLink:
            print('Unable find prod link for {}'.format(url))
        else:
            data_dict['prodLink'] = prodLink.attrs['href']

        # load date
        data_dict['loadDate'] = time.strftime('%d.%m.%Y', time.localtime())
        data_dict['webSiteID'] = self.webSiteID
        data_dict['categoryName'] = self.categoryName
        data_dict['categoryNameID'] = self.categoryNameId
        return data_dict


class Quelle(Card):
    def get_data(self, soup, url):
        # brand
        data_dict = {}
        html_classes = [{'class_name': 'product-brand', 'type': 'span'}]
        brandName = sf.clear_string(self._get_field_value(soup, html_classes, 'brand', url), sf.rus_letters + sf.lat_letters + sf.digits + sf.puncts + ' ')
        if brandName: data_dict['brandName'] = brandName

        # good type
        html_classes = [{'class_name': 'product-name', 'type': 'span'}]
        prodType = self._get_field_value(soup, html_classes, 'good type', url)
        if prodType: data_dict['prodType'] = sf.clear_string(prodType, sf.rus_letters + sf.lat_letters + sf.puncts + sf.digits + ' ')

        # full price and disc price
        price_soup = soup.find('div','q-product-price-box')
        if price_soup:
            for i in range(0,len(price_soup.contents)):
                if hasattr(price_soup.contents[i],'text'):
                    possible_price = sf.clear_string(price_soup.contents[i].text,sf.digits)
                    if sf.is_digit(possible_price):
                        if not data_dict.get('fullPrice'):
                            data_dict['fullPrice'] = int(possible_price)
                        else:
                            data_dict['discPrice'] = int(possible_price)
                            break
        else:
            print('Unable get the price for {}'.format(data_dict.get('brandName')))

        # prod link
        prodLink = soup.find('a', 'ddl_product_link')
        if not prodLink:
            print('Unable find prod link for {}'.format(url))
        else:
            data_dict['prodLink'] = prodLink.attrs['href']

        # load date
        data_dict['loadDate'] = time.strftime('%d.%m.%Y', time.localtime())
        data_dict['webSiteID'] = self.webSiteID
        data_dict['categoryName'] = self.categoryName
        data_dict['categoryNameID'] = self.categoryNameId
        return data_dict