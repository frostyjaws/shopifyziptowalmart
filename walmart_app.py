
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
import argparse
import time
from datetime import datetime

# === WALMART CREDENTIALS ===
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"

# === CONFIG ===
SHOPIFY_CSV_PATH = "products_export.csv"
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"
WALMART_FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
WALMART_FEED_STATUS_URL = "https://marketplace.walmartapis.com/v3/feeds/{}"

STATIC_DESCRIPTION = "<p>Celebrate the arrival of your little one...</p>"
BULLET_POINTS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> ...",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> ...",
    "👶 <strong>Comfort and Convenience:</strong> ...",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> ...",
    "📏 <strong>Versatile Sizing & Colors:</strong> ..."
]
FORCED_IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801.jpg"
]
variation_map = {
    "Newborn White Short Sleeve": "Newborn White Short Sleeve",
    "Newborn Natural Short Sleeve": "Newborn Natural Short Sleeve",
    "Newborn White Long Sleeve": "Newborn White Long Sleeve",
    "0-3M White Long Sleeve": "0-3M White Long Sleeve",
    "3-6M White Long Sleeve": "3-6M White Long Sleeve",
    "0-3M White Short Sleeve": "0-3M White Short Sleeve",
    "0-3M Pink Short Sleeve": "0-3M Pink Short Sleeve",
    "0-3M Blue Short Sleeve": "0-3M Blue Short Sleeve",
    "3-6M White Short Sleeve": "3-6M White Short Sleeve",
    "3-6M Pink Short Sleeve": "3-6M Pink Short Sleeve",
    "3-6M Blue Short Sleeve": "3-6M Blue Short Sleeve",
    "6M Natural Short Sleeve": "6M Natural Short Sleeve",
    "6-9M White Short Sleeve": "6-9M White Short Sleeve",
    "12M White Short Sleeve": "12M White Short Sleeve",
}

def build_walmart_xml(shopify_df):
    grouped = shopify_df.groupby("Handle")
    ns = "http://walmart.com/"
    ET.register_namespace("", ns)
    root = ET.Element("{%s}ItemFeed" % ns)

    for handle, group in grouped:
        title = group['Title'].iloc[0]
        smart_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"
        images = group[['Image Src', 'Image Position']].dropna().sort_values(by='Image Position')
        if images.empty:
            continue
        main_image = images.iloc[0]['Image Src']
        variant_group_id = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]

        for _, row in group.iterrows():
            raw_var = str(row.get("Option1 Value", "")).strip()
            mapped = variation_map.get(raw_var)
            if not mapped:
                continue
            try:
                size, color, sleeve = mapped.split(" ", 2)
            except ValueError:
                continue
            price = row.get("Variant Price", 0)
            quantity = int(float(row.get("Variant Inventory Qty", 1)))
            short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
            sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

            item = ET.SubElement(root, "Item")
            ET.SubElement(item, "sku").text = sku
            ET.SubElement(item, "productName").text = smart_title
            ET.SubElement(item, "productIdType").text = "GTIN"
            ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
            ET.SubElement(item, "manufacturerPartNumber").text = sku
            ET.SubElement(item, "price").text = f"{price:.2f}"
            ET.SubElement(item, "brand").text = BRAND
            ET.SubElement(item, "mainImageUrl").text = main_image
            for i, img in enumerate(FORCED_IMAGES):
                ET.SubElement(item, f"additionalImageUrl{i+1}").text = img
            ET.SubElement(item, "longDescription").text = STATIC_DESCRIPTION + "".join([f"<p>{bp}</p>" for bp in BULLET_POINTS])
            ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
            ET.SubElement(item, "variantGroupId").text = variant_group_id
            ET.SubElement(item, "swatchImageUrl").text = main_image
            ET.SubElement(item, "IsPreorder").text = IS_PREORDER
            ET.SubElement(item, "productType").text = PRODUCT_TYPE
            ET.SubElement(item, "quantity").text = str(quantity)

    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

def get_access_token():
    response = requests.post(
        "https://marketplace.walmartapis.com/v3/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    response.raise_for_status()
    return response.json()["access_token"]

def submit_feed(xml_data, token):
    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": "submit-" + str(random.randint(1000,9999)),
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml",
        "Content-Type": "application/xml"
    }
    res = requests.post(WALMART_FEED_URL, headers=headers, data=xml_data)
    res.raise_for_status()
    return res.text

def track_feed(feed_id, token):
    url = WALMART_FEED_STATUS_URL.format(feed_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "WM_SVC.NAME": "Walmart Marketplace"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Run full upload")
    parser.add_argument("--dry-run", action="store_true", help="Generate XML but don't submit")
    parser.add_argument("--track-feed", type=str, help="Check status of a Walmart feed ID")
    args = parser.parse_args()

    if args.track_feed:
        token = get_access_token()
        print("🔍 Checking feed status...")
        print(track_feed(args.track_feed, token))

    elif args.dry_run:
        print("🧪 Generating Walmart XML (dry run)...")
        df = pd.read_csv(SHOPIFY_CSV_PATH).dropna(subset=["Handle"])
        xml_output = build_walmart_xml(df)
        name = f"walmart_feed_DRYRUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(name, "w", encoding="utf-8") as f:
            f.write(xml_output)
        print(f"✅ Dry run complete. XML saved as {name}")

    elif args.run:
        print("🚀 Running full Walmart feed upload...")
        df = pd.read_csv(SHOPIFY_CSV_PATH).dropna(subset=["Handle"])
        xml_output = build_walmart_xml(df)
        name = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(name, "w", encoding="utf-8") as f:
            f.write(xml_output)
        print(f"📄 XML feed generated: {name}")
        token = get_access_token()
        response = submit_feed(xml_output, token)
        print("✅ Feed submitted successfully!")
        print(response)
    else:
        print("⚠️ Please use one of: --run, --dry-run, or --track-feed FEED_ID")
