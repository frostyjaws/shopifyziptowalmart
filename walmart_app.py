
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
from datetime import datetime

# === WALMART CREDENTIALS ===
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"

# === STATIC VALUES ===
SHOPIFY_CSV_PATH = "products_export.csv"
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"
WALMART_FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"

STATIC_DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world...</p>
"""

BULLET_POINTS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing, ensuring that your baby's outfit looks fantastic wash after wash.",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> Show your support for our heroes while dressing your little one in style with this adorable newborn romper from a veteran-owned small business.",
    "👶 <strong>Comfort and Convenience:</strong> Crafted from soft, breathable materials, this Bodysuit provides maximum comfort for your baby. Plus, the convenient snap closure makes diaper changes a breeze.",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> This funny Baby Bodysuit makes for an excellent baby shower gift or a thoughtful present for any new parents. It's a sweet and meaningful addition to any baby's wardrobe.",
    "📏 <strong>Versatile Sizing & Colors:</strong> Available in a range of sizes and colors, ensuring the perfect fit. Check our newborn outfit boy and girl sizing guide to find the right one for your little one."
]

FORCED_IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.com-webp-to-jpg-converter.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801d190d7fcdd5d2cce9576aa8de.jpg"
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
            long_desc = STATIC_DESCRIPTION + "".join([f"<p>{bp}</p>" for bp in BULLET_POINTS])
            ET.SubElement(item, "longDescription").text = long_desc
            ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
            ET.SubElement(item, "variantGroupId").text = variant_group_id
            ET.SubElement(item, "swatchImageUrl").text = main_image
            ET.SubElement(item, "IsPreorder").text = IS_PREORDER
            ET.SubElement(item, "productType").text = PRODUCT_TYPE
            ET.SubElement(item, "quantity").text = str(quantity)

    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

def get_access_token():
    url = "https://marketplace.walmartapis.com/v3/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    return response.json()["access_token"]

def submit_feed(xml_data, token):
    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": f"submit-{random.randint(1000,9999)}",
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml",
        "Content-Type": "application/xml"
    }
    response = requests.post(WALMART_FEED_URL, headers=headers, data=xml_data)
    response.raise_for_status()
    return response.text

if __name__ == "__main__":
    print("📥 Reading Shopify CSV...")
    shopify_df = pd.read_csv(SHOPIFY_CSV_PATH)
    shopify_df = shopify_df.dropna(subset=["Handle"])

    print("🧠 Generating Walmart XML with inventory...")
    xml_output = build_walmart_xml(shopify_df)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xml_filename = f"walmart_feed_{timestamp}.xml"
    with open(xml_filename, "w", encoding="utf-8") as f:
        f.write(xml_output)
    print(f"✅ XML feed saved: {xml_filename}")

    print("🔐 Authenticating with Walmart...")
    token = get_access_token()
    print("✅ Authenticated!")

    print("📤 Submitting feed to Walmart...")
    response = submit_feed(xml_output, token)
    print("✅ Feed submitted successfully!")
    print("📦 Walmart Response:")
    print(response)
