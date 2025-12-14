from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import random
from urllib.parse import quote
def set_up_selenium():
    # Chromeドライバを起動（ヘッドレスモード推奨）
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

def serch_picture_by_selenium(driver,query,settings):
    get_max_picture = settings["GET_MAX_PICTURE"]
    
    # Google画像検索ページを開く
    driver.get(f"https://www.google.com/search?tbm=isch&q={query}")

    # ページ読み込み待機
    sleep(2)

    # 画像を取得（imgタグを順に取得）
    result_html = driver.find_element(By.ID, "rso")
    images_html = result_html.find_elements(By.TAG_NAME, "img")
    images_html = images_html[:get_max_picture]
    images_url = [x.get_attribute('src') for x in images_html]

    # get_max_picture枚の画像URLを抽出
    return images_url


def search_picture_by_yahoo(driver, query):
    # クエリをURLエンコード（UTF-8）
    encoded_query = quote(query)

    # Yahoo!画像検索を開く
    driver.get(f"https://search.yahoo.co.jp/image/search?p={encoded_query}")
    sleep(1)

    # ページを少しスクロールして画像を読み込む
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    sleep(1)

    # 画像要素を取得
    image_elements = driver.find_elements(By.CLASS_NAME, "sw-Thumbnail__image.sw-Thumbnail__image--tile")

    # 最初の10件を取得し、ランダムな順番に並べ替える
    sample_elements = image_elements[:10]
    random.shuffle(sample_elements)

    picture_urls = []

    for elem in sample_elements:
        try:
            elem.click()
            sleep(1)

            new_pic_elem = driver.find_element(By.CLASS_NAME, "sw-PreviewPanel__imageBlock")
            new_pic_elem = new_pic_elem.find_element(By.TAG_NAME, "img")

            src = new_pic_elem.get_attribute("src")
            width = new_pic_elem.get_attribute("naturalWidth")
            height = new_pic_elem.get_attribute("naturalHeight")

            # 画像サイズの短辺が400以上であることを確認
            if src and width and height:
                width = int(width)
                height = int(height)
                if min(width, height) >= 400:
                    picture_urls.append(src)

            # 3件集まったら終了
            if len(picture_urls) >= 3:
                break

        except Exception as e:
            # 要素が見つからない場合などを無視して次へ
            continue

    return picture_urls