import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *
import pymongo
from pyquery import PyQuery as pq

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

broswer = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(broswer, 10)


def search():
    print("Searching")
    try:
        broswer.get('https://www.taobao.com/')
        input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@class='search-combobox-input']"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        input.send_keys('美食')
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='total']"))
        )
        get_products_info()
        return total.text
    except TimeoutException:
        return search()


def get_products_info():
    wait.until(
        EC.presence_of_element_located((By.ID, "mainsrp-itemlist"))
    )
    page_html = broswer.page_source
    doc = pq(page_html)
    items = doc("#mainsrp-itemlist .items .item").items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'shop': item.find('.shop').text(),
            'deal_count': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo_db(product)


def save_to_mongo_db(result):
    try:
        if db[MONGO_TABLE].insert_one(result):
            print("Save to mongo DB Succeed!", result)
    except Exception:
        print("Save Failed", result)


def next_page(page_number):
    print("Next Page...")
    try:
        page_number_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='number']"))
        )
        page_number_input.clear()
        page_number_input.send_keys(str(page_number))
        confirm_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='form']/span[text()='确定']"))
        )
        confirm_button.click()
        wait.until(
            EC.text_to_be_present_in_element((By.XPATH, "//li[@class='item active']/span"), str(page_number))
        )
        get_products_info()
    except TimeoutException:
        next_page(page_number)


def main():
    try:
        total = search()

        total_number = int(re.compile('\d+').search(total).group(0))
        print(total_number)
        for i in range(2, 3):
            next_page(i)
    finally:
        broswer.quit()


if __name__ == '__main__':
    main()



