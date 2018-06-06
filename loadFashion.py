from fashionSites import *
import sqlite3 as sql
from paths import *


main_conn = sql.connect(mainDbasePath)
cr_conn = sql.connect(crDbasePath)
main_c = main_conn.cursor()
cr_c = cr_conn.cursor()

# main_c.execute('UPDATE links SET isChecked=0')
rows = main_c.execute('SELECT id,link,webSiteId,categoryName FROM links')
driver = webdriver.Chrome(driverPath)
for row in rows.fetchall():
    link_id = row[0]
    link = row[1]
    web_site_id = row[2]
    category_name = row[3]
    web_site = None
    if web_site_id == 1:
        web_site = WebSite_Wildberries(link,  driver, category_name, link_id, cr_conn)
    elif web_site_id == 2:
        web_site = WebSite_Lamoda(link,  driver, category_name, link_id, cr_conn)
    elif web_site_id == 3:
        web_site = WebSite_Kupivip(link,  driver, category_name, link_id, cr_conn)
    elif web_site_id == 4:
        web_site = WebSite_Bonprix(link,  driver, category_name, link_id, cr_conn)
    elif web_site_id == 5:
        web_site = WebSite_Quelle(link,  driver, category_name, link_id, cr_conn)
    # get data
    web_site.make_test()
    web_site.get_all_cards()
    web_site.save_cards()
    main_c.execute('UPDATE links SET isChecked=2 WHERE id={}'.format(link_id))
    main_conn.commit()
driver.close()
print('Creating a pivot table')
cr_c.execute("CREATE TABLE `pivot` ( `webSiteID` INTEGER, `categoryName` TEXT, `cntItems` INTEGER )")
cr_conn.commit()
cr_c.execute("INSERT INTO pivot SELECT websiteid,categoryname,count(id) FROM prodData GROUP BY websiteid, categoryname")
cr_conn.commit()
