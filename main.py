import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_hepsiburada(search_term="kulaklik"):
    base_url = "https://www.hepsiburada.com"
    url = f"https://www.hepsiburada.com/ara?q={search_term}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_cards = soup.find_all("li", class_="productListContent-zAP0Y5msy8OHn5z7T_K_")

    products = []

    for card in product_cards:
        try:
            title = card.find("h2", class_="title-module_titleRoot__dNDiZ").get_text(strip=True)
            price_str = card.find("div", class_="price-module_finalPrice__LtjvY").get_text(strip=True)
            price = float(price_str.replace("TL", "").replace(".", "").replace(",", "."))
            
            tag = card.find("a", class_="productCardLink-module_productCardLink__GZ3eU")

            #get product link
            if tag and "href" in tag.attrs:
                product_link = base_url + tag["href"]    
                # get product page
                product_response = requests.get(product_link, headers=headers)
                product_soup = BeautifulSoup(product_response.text, 'html.parser')
                product_class = product_soup.find("span", class_="rzVCX6O5Vz9bkKB61N2W")
                seller_str = product_class.get_text(strip=True)


            products.append({
                "Ürün Adı": title,
                "Fiyat (TL)": price,
                "Satıcı": seller_str,
                "Site": "Hepsiburada",
                "Bağlantı": product_link
            })
        except Exception as e:
            #print("Hepsiburada atlandı (reklam):", e)
            continue

    return products


def find_min_price(s):
    # Eğer "Sepette" varsa kaldır
    s = s.replace("Sepette", "").strip()
    
    # Boşlukla ayrılmış parçalara ayır
    parts = s.split()
    
    # İki tane sayı varsa
    if len(parts) == 2 or len(parts) == 1:
        try:
            # Sayıları float'a çevir ve minimumu döndür
            nums = [float(p) for p in parts]
            return min(nums)
        except ValueError:
            # Sayıya çevrilemiyorsa None döndür
            return None
    else :
        return None

def scrape_trendyol(search_term="kulaklik"):
    base_url = "https://www.trendyol.com"
    search_url = f"{base_url}/sr?q={search_term}"

    # ChromeDriver otomatik kurulum
    chromedriver_autoinstaller.install()

    # Başlatma ayarları
    options = Options()
    options.add_argument("--headless=new")  # Arka planda çalışsın
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 ...")

    driver = webdriver.Chrome(options=options)
    driver.get(search_url)

    try:
        # Ürün kartlarını bekle (max 10 saniye)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "p-card-wrppr"))
        )
    except Exception as e:
        print("Ürünler yüklenmedi:", e)

    # Sayfa kaynağını al
    soup = BeautifulSoup(driver.page_source, "html.parser")
    

    products = []
    product_cards = soup.find_all("div", class_="p-card-wrppr")
    print("Bulunan ürün sayısı:", len(product_cards))

    for card in product_cards:
        try:
            link_tag = card.find("a", class_="p-card-chldrn-cntnr card-border")
            #get product link
            if link_tag and "href" in link_tag.attrs:
                product_link = base_url + link_tag["href"]
                driver.get(product_link)
                # get product page
                product_soup = BeautifulSoup(driver.page_source, "html.parser")
                product_class = product_soup.find("a", class_="seller-name-text")
                seller_str = product_class.get_text(strip=True)


            brand_tag = card.find("span", class_="prdct-desc-cntnr-ttl")
            name_tag = card.find("span", class_="prdct-desc-cntnr-name")
            desc_tag = card.find("div", class_="product-desc-sub-text")

            brand = brand_tag.text.strip() if brand_tag else ""
            name = name_tag.text.strip() if name_tag else ""
            desc = desc_tag.text.strip() if desc_tag else ""
            full_name = f"{brand} {name} {desc}".strip()
           
            price_tag = card.find("div", class_="price-information") # price-item basket-price-original  price-item discounted
            if price_tag:
                price_text = (
                    price_tag.text.strip()
                    .replace(".", "")
                    .replace(",", ".")
                    .replace("TL", "")
                )
                price = find_min_price(price_text)
            else:
                price = None

            if price:
                products.append({
                    "Ürün Adı": full_name,
                    "Fiyat (TL)": price,
                    "Satıcı": seller_str,
                    "Site": "Trendyol",
                    "Bağlantı": product_link
                })
        except Exception as e:
            print("Ürün atlandı:", e)
            continue
    driver.quit()      
    return products





if __name__ == "__main__":
    search_term = input('What do you want to search for: ')
    
    service = input("Choose your service: hepsiburada or trendyol: ").lower()
    
    products = None

    if service == "hepsiburada":
        print("Scraping from Hepsiburada ...")
        products = scrape_hepsiburada(search_term)
    elif service == "trendyol":
        print("Scraping from Trendyol...")
        products = scrape_trendyol(search_term)
    else:
        print("Service is not found!")
        exit()



    df = pd.DataFrame(products)
    df.to_csv('products.csv', index=False, encoding='utf-8-sig', sep=";")

    print("\n💰 Top 5 Cheapest Products:")
    print(df.sort_values("Fiyat (TL)").head(5))

    print("\n💸 Top 5 most expensive products:")
    print(df.sort_values("Fiyat (TL)", ascending=False).head(5))