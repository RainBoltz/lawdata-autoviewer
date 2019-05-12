from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import numpy as np
import requests as req
import sys, time, os

# 登入
init_url = 'http://sw.library.ntpu.edu.tw:81/menu'
username = sys.argv[1]
password = sys.argv[2]

# 搜尋項目
law_url = 'http://sw.library.ntpu.edu.tw:81/login?url=http://www.lawdata.com.tw'
next_page_xpath = '//img[@title="次頁"]/parent::a' #NoSuchElementException
open_reader_xpath = '//img[@title="PNG全文"]/parent::a'
journal_only_xpath = '//a[@class="global" and @href[contains(.,"^^^3")]]'
with open('terms.txt', 'r') as f:
    terms = f.readlines()
terms = [x.strip() for x in terms]

# 影像相關
img_base_url = 'http://www.lawdata.com.tw.sw.library.ntpu.edu.tw:81'
next_img_xpath = '//img[@title="下一頁"]/parent::a' #NoSuchElementException
img_xpath = '/html/body/center/table/tbody/tr[2]/td/table' #background
def download_img(url, cookies, fname):
    s = req.session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'})
    for cookie in cookies:
        c = {cookie['name']: cookie['value']}
        s.cookies.update(c)
        r = s.get(url, allow_redirects=True)
        with open(fname + '.png', 'wb') as f:
            f.write(r.content)



# 開始
driver = webdriver.Chrome()
driver.get(init_url)

driver.find_element_by_name('user').send_keys(username)
driver.find_element_by_name('pass').send_keys(password)
time.sleep(1)
driver.find_element_by_xpath('//input[@type="submit"]').click()

if not os.path.exists("download"):
    os.makedirs("download")
for term in terms:
    driver.get(law_url)

    driver.find_element_by_name('TOPTERM').send_keys(term)
    time.sleep(1)
    driver.find_element_by_name('_IMG_查詢').click()

    main_window = driver.window_handles[0]
    while True:
        time.sleep(3)
        try:
            select_journal = driver.find_element_by_xpath(journal_only_xpath)
            select_journal.click()
        except NoSuchElementException as e:
            print('ERROR: 沒有期刊！')
            break
        try:
            _ = driver.find_elements_by_xpath(open_reader_xpath)
        except NoSuchElementException as e:
            print('ERROR: 沒有結果！')
            break

        for reader in driver.find_elements_by_xpath(open_reader_xpath):
            cols = reader.find_elements_by_xpath('parent::td/parent::tr/td')[1:-1] #中文篇名, 中文刊名, 作者, 出版年月
            full_name = "___".join([ col.text for col in cols ])
            if not os.path.exists("{}/{}".format("download",full_name)):
                os.makedirs("{}/{}".format("download",full_name))
            print(full_name)

            reader.click()
            # new window start
            time.sleep(2)
            driver.switch_to_window(driver.window_handles[-1])
            ans = ""
            for n in driver.find_elements_by_xpath('//img[@border="0"]'):
                ans += n.get_attribute('src').split('/')[-1].replace('.gif','').replace('n','')
            time.sleep(1)
            driver.find_element_by_xpath('//input[@name="RAND"]').send_keys(ans)
            driver.find_element_by_xpath('//input[@name="_TTS.BUTTON"]').click()
            img_N = 1
            while True:
                time.sleep(2)
                img_url = img_base_url + driver.find_element_by_xpath(img_xpath).get_attribute('background')
                download_img(img_url, driver.get_cookies(), "%s/%s/%03d"%("download",full_name,img_N))
                img_N += 1
                time.sleep(1)
                try:
                    next_img = driver.find_element_by_xpath(next_img_xpath)
                    next_img.click()
                except NoSuchElementException as e:
                    break
            driver.close()
            driver.switch_to_window(main_window)
            # new window end
        try:
            next_page = driver.find_element_by_xpath(next_page_xpath)
            next_page.click()
        except NoSuchElementException as e:
            break
    time.sleep(3)

driver.quit()
    
            




