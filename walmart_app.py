import requests
import xml.etree.ElementTree as ET
import csv
import random
from datetime import datetime
from io import StringIO

# Sandbox API credentials
CLIENT_ID = '21fbdc27-d571-496e-bddb-6e99029a630d'
CLIENT_SECRET = 'Y6vpggBcEWlY5OO23ewnYO2yctcPTo3m0abpoqMLWK-dklh34LyK961yTAAuTn5mGpIARtRE1qZqn-QD6V0hww'

# Walmart Sandbox API endpoints
TOKEN_URL = 'https://sandbox.walmartapis.com/v3/token'
FEED_URL = 'https://sandbox.walmartapis.com/v3/feeds?feedType=MP_ITEM'

# Master variations and prices
MASTER_VARIATIONS = {
    "Newborn White Short Sleeve": 27.99,
    "Newborn White Long Sleeve": 28.99,
    "Newborn (0-3M) Natural Short Sleeve": 31.99,
    "0-3M White Short Sleeve": 27.99,
    "0-3M White Long Sleeve": 28.99,
    "0-3M Pink Short Sleeve": 31.99,
    "0-3M Blue Short Sleeve": 31.99,
    "3-6M White Short Sleeve": 27.99,
    "3-6M White Long Sleeve": 28.99,
    "3-6M Pink Short Sleeve": 31.99,
    "3-6M Blue Short Sleeve": 31.99,
    "6-9M White Short Sleeve": 27.99,
    "6M Natural Short Sleeve": 31.99
}

ADDITIONAL_IMAGE_URLS = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_39118440-7324-4737-a9b6-9bc4e9dab73d.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_32129b22-54df-4f68-8da7-30b93a0e85cc.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_07aeb493-bfd6-40d8-809d-709037313156.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/1a38365ed663e060d2590b04a0ec16b00004fe45_f8aaa5cc-0182-4bf8-9ada-860c6d175f25.jpg?v=1740931622"
]

def generate_sku(title, variation):
    base = ''.join(e for e in title if e.isalnum())[:25]
    color = next((c for c in ["White", "Pink", "Blue", "Natural"] if c in variation), "X")
    size = variation.split()[0].replace("(", "").replace(")", "").replace("M", "M").replace("Newborn", "NB").replace("6-9M", "6_9M").replace("6M", "6M")
    sleeve = "Long" if "Long" in variation else "Short"
    rand = random.randint(100, 999)
    return f"{base}-{size}-{color}-{sleeve}-{rand}"

def build_walmart_xml(file_content):
    tree = ET.Element("WalmartEnvelope")
    ET.SubElement(tree, "xmlns").text = "http://walmart.com/"
    header = ET.SubElement(tree, "Header")
    ET.SubElement(header, "version").text = "1.4"
    ET.SubElement(header, "requestId").text = "123456789"
    ET.SubElement(header, "requestType").text = "MP_ITEM"
    feed_header = ET.SubElement(tree, "MPItemFeedHeader")
    ET.SubElement(feed_header, "locale").text = "en"
    ET.SubElement(feed_header, "sellingChannel").text = "marketplace"

    reader = csv.DictReader(StringIO(file_content.decode("utf-8")))
    for row in reader:
        title = row["Title"].strip()
        image = row["Image Src"].strip()

        for variation, price in MASTER_VARIATIONS.items():
            sku = generate_sku(title, variation)
            mp_item = ET.SubElement(tree, "MPItem")
            ET.SubElement(mp_item, "sku").text = sku
            ET.SubElement(mp_item, "productName").text = f"{title} - {variation}"
            ET.SubElement(mp_item, "productId").text = "EXEMPT"
            ET.SubElement(mp_item, "productIdType").text = "GTIN"
            ET.SubElement(mp_item, "price").text = f"{price:.2f}"
            ET.SubElement(mp_item, "productTaxCode").text = "2038710"
            ET.SubElement(mp_item, "category").text = "Baby > Apparel > Bodysuits"
            ET.SubElement(mp_item, "description").text = f"Funny baby bodysuit: {title}"
            ET.SubElement(mp_item, "brand").text = "NOFO VIBES"
            ET.SubElement(mp_item, "mainImageUrl").text = image
            for i, url in enumerate(ADDITIONAL_IMAGE_URLS):
                ET.SubElement(mp_item, f"additionalImageUrl{i+1}").text = url
            ET.SubElement(mp_item, "shippingWeight").text = "0.2 lb"
            ET.SubElement(mp_item, "fulfillmentLagTime").text = "2"
            ET.SubElement(mp_item, "productType").text = "Clothing"
            ET.SubElement(mp_item, "minAdvertisedPrice").text = f"{price:.2f}"
            ET.SubElement(mp_item, "mustShipAlone").text = "No"
            ET.SubElement(mp_item, "quantity").text = str(999)

    filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    ET.ElementTree(tree).write(filename, encoding="utf-8", xml_declaration=True)
    return filename

def get_access_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def submit_feed(xml_file_path, access_token):
    headers = {
        'WM_SVC.NAME': 'Walmart Marketplace',
        'WM_QOS.CORRELATION_ID': '123456abcdef',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/xml',
        'Content-Type': 'application/xml'
    }
    with open(xml_file_path, 'rb') as file:
        response = requests.post(FEED_URL, headers=headers, data=file)
    response.raise_for_status()
    return response.json()

def check_feed_status(feed_id, access_token):
    status_url = f'https://sandbox.walmartapis.com/v3/feeds/{feed_id}'
    headers = {
        'WM_SVC.NAME': 'Walmart Marketplace',
        'WM_QOS.CORRELATION_ID': '123456abcdef',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    response = requests.get(status_url, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage:
# file_content = open('your_shopify_csv.csv', 'rb').read()
# xml_file = build_walmart_xml(file_content)
# token = get_access_token()
# submission_response = submit_feed(xml_file, token)
# feed_id = submission_response['feedId']
# status = check_feed_status(feed_id, token)
# print(status)
