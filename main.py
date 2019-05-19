from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
with open('terms.txt', 'r', encoding="utf-8-sig") as f:
    terms = f.readlines()
terms = [x.strip() for x in terms]

# 影像相關
SAVE_PATH = r"download"
img_base_url = 'http://www.lawdata.com.tw.sw.library.ntpu.edu.tw:81'
next_img_xpath = '//img[@title="下一頁"]/parent::a' #NoSuchElementException
img_xpath = '/html/body/center/table/tbody/tr[2]/td/table' #background
def download_img(url, cookies, fname):
    s = req.session()
    s.headers.update({'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'})
    for cookie in cookies:
        c = {cookie['name']: cookie['value']}
        s.cookies.update(c)
        r = s.get(url, allow_redirects=True)
        with open(fname + '.png', 'wb') as f:
            f.write(r.content)
def naming_escapes(fname):
    escapes = {
        ":": "：",
        "/": "／",
        "\\": "＼",
        "*": "＊",
        ">": "＞",
        "<": "＜",
        "\"": "＂",
        "?": "？",
        "|": "｜"
    }
    for ch in escapes:
        fname = fname.replace(ch, escapes[ch])
    return fname


# 開始
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get(init_url)

driver.find_element_by_name('user').send_keys(username)
driver.find_element_by_name('pass').send_keys(password)
time.sleep(1)
driver.find_element_by_xpath('//input[@type="submit"]').click()

rest_countdown = 100

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)
for term in terms:
    print('關鍵字：%s'%term)
    driver.get(law_url)

    driver.find_element_by_name('TOPTERM').send_keys(term)
    time.sleep(1)
    driver.find_element_by_name('_IMG_查詢').click()

    try:
        select_journal = driver.find_element_by_xpath(journal_only_xpath)
        select_journal.click()
    except NoSuchElementException as e:
        print('\t沒有期刊！')
        time.sleep(1)
        continue

    main_window = driver.window_handles[0]
    page_cnt = 1
    while True:
        print("\t抓取第 %02d 頁"%page_cnt)
        time.sleep(10)
        
        HAS_RESULT_FLAG = True
        try:
            _ = driver.find_elements_by_xpath(open_reader_xpath)
        except NoSuchElementException as e:
            print('\t\t沒有結果！')
            HAS_RESULT_FLAG = False
        
        if HAS_RESULT_FLAG:
            results = driver.find_elements_by_xpath(open_reader_xpath)
            print('\t\t%02d 個搜尋結果...'%len(results))
            for reader in results:
                cols = reader.find_elements_by_xpath('parent::td/parent::tr/td')[1:-1] #中文篇名, 中文刊名, 作者, 出版年月
                full_name = "___".join([ col.text for col in cols ])
                full_name = naming_escapes(full_name) #避免資料夾出錯
                if not os.path.exists("{}/{}".format(SAVE_PATH,full_name)):
                    os.makedirs("{}/{}".format(SAVE_PATH,full_name))
                else:
                    continue

                reader.click()
                # new window start
                time.sleep(5)
                driver.switch_to_window(driver.window_handles[-1])
                ans = ""
                for n in driver.find_elements_by_xpath('//img[@border="0"]'):
                    ans += n.get_attribute('src').split('/')[-1].replace('.gif','').replace('n','')
                time.sleep(1)
                driver.find_element_by_xpath('//input[@name="RAND"]').send_keys(ans)
                driver.find_element_by_xpath('//input[@name="_TTS.BUTTON"]').click()
                img_N = 1
                while True:
                    time.sleep(np.random.choice([4,5,6]))
                    img_url = img_base_url + driver.find_element_by_xpath(img_xpath).get_attribute('background')
                    download_img(img_url, driver.get_cookies(), "%s/%s/%03d"%(SAVE_PATH,full_name,img_N))
                    
                    # 如果一段時間內超過某流量就會被鎖 (目前未知)
                    rest_countdown -= 1
                    if rest_countdown == 0:
                        rest_countdown = 150
                        time.sleep(60*30)
                    
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
            page_cnt += 1
        except NoSuchElementException as e:
            break
    time.sleep(10)

driver.quit()
    
            



