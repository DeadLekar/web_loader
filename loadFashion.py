from fashionSites import *
import sqlite3 as sql
from paths import *


main_conn = sql.connect(mainDbasePath)
cr_conn = sql.connect(crDbasePath)
main_c = main_conn.cursor()
cr_c = cr_conn.cursor()



rows = main_c.execute('SELECT id,link,webSiteId,categoryName FROM links WHERE isChecked=0')
for row in rows.fetchall():
    id = row[0]
    link = row[1]
    web_site_id = row[2]
    category_name = row[3]
    card = None
    cards_html_classes = []
    next_page_xpath = ''
    next_page_html = ''
    next_page_text = ''
    if web_site_id == 1:
        card = Wildberries(web_site_id, category_name)
        cards_html_classes = [{'class_name': 'dtList', 'type': 'div'}]
        next_page_html = 'next'
    elif web_site_id == 2:
        card = Lamoda(web_site_id, category_name)
        cards_html_classes = [{'class_name': 'products-list-item', 'type': 'div'}]
        next_page_html = 'paginator__next'
    elif web_site_id == 3:
        card = Kupivip(web_site_id, category_name)
        cards_html_classes = [{'class_name': 'product-item', 'type': 'div'}]
        next_page_html = 'icon-arrow right'
    elif web_site_id == 4:
        card = Bonprix(web_site_id, category_name)
        cards_html_classes = [{'class_name': 'product-list-item ', 'type': 'div'}]
        next_page_html = 'next'
    elif web_site_id == 5:
        card = Quelle(web_site_id, category_name)
        cards_html_classes = [{'class_name': 'q-product-box', 'type': 'li'}]
        next_page_html = 'pagination-next'


    # get data
    web_site = WebSite(link, driverPath, web_site_id, category_name, card, cards_html_classes, next_page_html, cr_conn)
    web_site.make_test()
    # web_site.get_all_cards()
    # web_site.save_cards()

print('Creating a pivot table')
cr_c.execute("CREATE TABLE `pivot` ( `webSiteID` INTEGER, `categoryName` TEXT, `cntItems` INTEGER )")
cr_conn.commit()
cr_c.execute("INSERT INTO pivot SELECT websiteid,categoryname,count(id) FROM prodData GROUP BY websiteid, categoryname")
cr_conn.commit()