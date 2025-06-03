import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
from datetime import datetime

# === WALMART API CREDENTIALS ===
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"

# === CONSTANTS ===
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"

STATIC_DESCRIPTION = (
    "<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, "
    "the perfect baby shower gift that will be cherished for years to come...</p>"
)

FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
STATUS_URL = "https://marketplace.walmartapis.com/v3/feeds/{}"

BULLETS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> Vibrant, long-lasting colors...",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> Support our heroes...",
    "👶 <strong>Comfort and Convenience:</strong> Soft, breathable materials...",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> Thoughtful present for new parents...",
    "📏 <strong>Versatile Sizing & Colors:</strong> Available in a range of sizes and colors..."
]

IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801.jpg"
]

fixed_variations = {
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

INVENTORY_FOR_ALL = 999

def get_token():
    try:
        url = "https://marketplace.walmartapis.com/v3/token?grant_type=client_credentials"
        response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"❌ Error getting access token: {e}")
        return None

def build_xml(df):
    try:
        required_cols = {"Title", "Handle", "Variant Inventory Qty", "Image Src", "Image Position"}
        if not required_cols.issubset(df.columns):
            raise ValueError("Missing required CSV columns.")

        ns = "http://walmart.com/"
        ET.register_namespace("", ns)
        root = ET.Element(f"{{{ns}}}ItemFeed")

        for handle, group in df.groupby("Handle"):
            title = group["Title"].iloc[0]
            display_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

            images = (
                group[["Image Src", "Image Position"]]
                .dropna()
                .sort_values(by="Image Position")
            )
            if images.empty:
                continue

            main_image = images.iloc[0]["Image Src"]
            group_id = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]

            for variation_name, price in fixed_variations.items():
                parts = variation_name.split(" ", 2)
                size, color, sleeve = (parts + ["", "", ""])[:3]
                short_handle = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]
                sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

                item = ET.SubElement(root, "Item")
                ET.SubElement(item, "sku").text = sku
                ET.SubElement(item, "productName").text = display_title
                ET.SubElement(item, "productIdType").text = "GTIN"
                ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
                ET.SubElement(item, "manufacturerPartNumber").text = sku
                ET.SubElement(item, "price").text = f"{price:.2f}"
                ET.SubElement(item, "brand").text = BRAND
                ET.SubElement(item, "mainImageUrl").text = main_image

                for img_url in IMAGES[:5]:
                    ET.SubElement(item, "additionalImageUrl").text = img_url

                description = STATIC_DESCRIPTION + "".join(f"<p>{b}</p>" for b in BULLETS)
                ET.SubElement(item, "longDescription").text = description
                ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
                ET.SubElement(item, "variantGroupId").text = group_id
                ET.SubElement(item, "swatchImageUrl").text = main_image
                ET.SubElement(item, "isPreorder").text = IS_PREORDER
                ET.SubElement(item, "category").text = "Fashion"
                ET.SubElement(item, "subCategory").text = "Baby Garments & Accessories"
                ET.SubElement(item, "productType").text = "Baby Bodysuits & One‐Pieces"

                inventory = ET.SubElement(item, "inventory")
                ET.SubElement(inventory, "quantity").text = str(INVENTORY_FOR_ALL)

        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    except Exception as e:
        st.error(f"❌ XML generation failed: {e}")
        return None

def submit_feed(xml: str, token: str) -> str:
    try:
        headers = {
            "WM_SVC.NAME": "Walmart Marketplace",
            "WM_QOS.CORRELATION_ID": f"submit-{random.randint(1000,9999)}",
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml",
            "Content-Type": "application/xml"
        }
        response = requests.post(FEED_URL, headers=headers, data=xml)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.error(f"❌ Submission failed: {e}")
        return None

def track_feed(feed_id: str, token: str) -> str:
    try:
        headers = {"Authorization": f"Bearer {token}", "WM_SVC.NAME": "Walmart Marketplace"}
        response = requests.get(STATUS_URL.format(feed_id), headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.error(f"❌ Feed tracking failed: {e}")
        return None

# === STREAMLIT UI ===
st.set_page_config(page_title="Walmart Product Feed Uploader", layout="wide")
st.title("🛒 Walmart Product Feed Uploader (Fixed Variations)")

if "generated_xml" not in st.session_state:
    st.session_state.generated_xml = None
if "xml_filename" not in st.session_state:
    st.session_state.xml_filename = None

uploaded = st.file_uploader("Upload your Shopify products_export.csv", type="csv")

feed_status_id = st.text_input("Enter Feed ID to track status:", placeholder="e.g. 1234567890")

if uploaded:
    try:
        df = pd.read_csv(uploaded)
        st.write("▶️ Detected columns:", list(df.columns))
        st.write(df.head(2))

        if st.button("🧠 Generate Walmart XML"):
            xml = build_xml(df)
            if xml:
                filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(xml)
                st.session_state.generated_xml = xml
                st.session_state.xml_filename = filename
                st.success("✅ XML Generated!")
                st.code(xml[:3000] + "...", language="xml")

        if st.session_state.generated_xml:
            with open(st.session_state.xml_filename, "rb") as f:
                st.download_button("📥 Download XML", f, file_name=st.session_state.xml_filename)

            if st.button("📤 Submit to Walmart"):
                token = get_token()
                if token:
                    result = submit_feed(st.session_state.generated_xml, token)
                    if result:
                        st.success("✅ Feed Submitted!")
                        st.code(result)

    except Exception as e:
        st.error(f"❌ Could not process CSV: {e}")

if feed_status_id:
    if st.button("🔍 Track Feed Status"):
        token = get_token()
        if token:
            result = track_feed(feed_status_id, token)
            if result:
                st.code(result)
