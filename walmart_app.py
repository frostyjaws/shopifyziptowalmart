
import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
from datetime import datetime
import os

# === WALMART API CREDENTIALS ===
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"

# === CONSTANTS ===
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"
STATIC_DESCRIPTION = "<p>Celebrate the arrival of your little one...</p>"
FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
STATUS_URL = "https://marketplace.walmartapis.com/v3/feeds/{}"

BULLETS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> ...",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> ...",
    "👶 <strong>Comfort and Convenience:</strong> ...",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> ...",
    "📏 <strong>Versatile Sizing & Colors:</strong> ..."
]
IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801.jpg"
]

VARIATIONS = {
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

# === FUNCTIONS ===
def get_token():
    res = requests.post(
        "https://marketplace.walmartapis.com/v3/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    res.raise_for_status()
    return res.json()["access_token"]

def build_xml(df):
    grouped = df.groupby("Handle")
    ns = "http://walmart.com/"
    ET.register_namespace("", ns)
    root = ET.Element("{%s}ItemFeed" % ns)

    for handle, group in grouped:
        title = group['Title'].iloc[0]
        display_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"
        images = group[['Image Src', 'Image Position']].dropna().sort_values(by='Image Position')
        if images.empty:
            continue
        main_image = images.iloc[0]['Image Src']
        group_id = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]

        for _, row in group.iterrows():
            raw = str(row.get("Option1 Value", "")).strip()
            mapped = VARIATIONS.get(raw)
            if not mapped:
                continue
            try:
                size, color, sleeve = mapped.split(" ", 2)
            except:
                continue
            price = row.get("Variant Price", 0)
            qty = int(float(row.get("Variant Inventory Qty", 1)))
            short = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
            sku = f"{short}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

            item = ET.SubElement(root, "Item")
            ET.SubElement(item, "sku").text = sku
            ET.SubElement(item, "productName").text = display_title
            ET.SubElement(item, "productIdType").text = "GTIN"
            ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
            ET.SubElement(item, "manufacturerPartNumber").text = sku
            ET.SubElement(item, "price").text = f"{price:.2f}"
            ET.SubElement(item, "brand").text = BRAND
            ET.SubElement(item, "mainImageUrl").text = main_image
            for i, img in enumerate(IMAGES):
                ET.SubElement(item, f"additionalImageUrl{i+1}").text = img
            desc = STATIC_DESCRIPTION + "".join([f"<p>{b}</p>" for b in BULLETS])
            ET.SubElement(item, "longDescription").text = desc
            ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
            ET.SubElement(item, "variantGroupId").text = group_id
            ET.SubElement(item, "swatchImageUrl").text = main_image
            ET.SubElement(item, "IsPreorder").text = IS_PREORDER
            ET.SubElement(item, "productType").text = PRODUCT_TYPE
            ET.SubElement(item, "quantity").text = str(qty)

    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

def submit_feed(xml, token):
    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": f"submit-{random.randint(1000,9999)}",
        "Authorization": f"Bearer {token}",
        "Accept": "application/xml",
        "Content-Type": "application/xml"
    }
    res = requests.post(FEED_URL, headers=headers, data=xml)
    res.raise_for_status()
    return res.text

def track_feed(feed_id, token):
    res = requests.get(
        STATUS_URL.format(feed_id),
        headers={"Authorization": f"Bearer {token}", "WM_SVC.NAME": "Walmart Marketplace"}
    )
    res.raise_for_status()
    return res.text

# === STREAMLIT UI ===
st.set_page_config(page_title="Walmart Uploader", layout="wide")
st.title("🛒 Walmart Product Feed Uploader")

uploaded = st.file_uploader("Upload Shopify products_export.csv", type="csv")
feed_status_id = st.text_input("Enter Feed ID to track status:")

if uploaded:
    df = pd.read_csv(uploaded)
    if st.button("🧠 Generate Walmart XML"):
        xml = build_xml(df)
        filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(xml)
        st.success("✅ XML Generated!")
        st.code(xml[:3000] + "...", language="xml")
        with open(filename, "rb") as f:
            st.download_button("📥 Download XML", f, file_name=filename)

        if st.button("📤 Submit to Walmart"):
            try:
                token = get_token()
                response = submit_feed(xml, token)
                st.success("✅ Feed Submitted!")
                st.code(response)
            except Exception as e:
                st.error(f"❌ Submission Failed: {e}")

if feed_status_id:
    if st.button("🔍 Track Feed Status"):
        try:
            token = get_token()
            result = track_feed(feed_status_id, token)
            st.code(result)
        except Exception as e:
            st.error(f"❌ Could not fetch feed status: {e}")
