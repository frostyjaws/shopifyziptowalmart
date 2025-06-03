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
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"
STATIC_DESCRIPTION = (
    "Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, the perfect baby shower gift that will be cherished for years to come. "
    "This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, "
    "or a special baby shower, this baby bodysuit is sure to delight.\n\n"
    "Our Custom Baby Bodysuit features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby bodysuit is "
    "designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.\n\n"
    "Perfect for both baby boys and girls, this versatile baby bodysuit is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps "
    "make changing a breeze, providing convenience for busy parents.\n\n"
    "Whether you're looking for a personalized baby bodysuit, a funny baby bodysuit, or a cute baby bodysuit, this Custom Baby Bodysuit has it all. It’s ideal for celebrating "
    "the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.\n\n"
    "From baby boy clothes to baby girl clothes, this baby bodysuit is perfect for any newborn. Whether it’s a boho design, a Fathers Day gift, or custom baby clothes, this piece "
    "is a wonderful addition to any baby's wardrobe.\n\n"
    "Get this Custom Baby Bodysuit today and let your little one showcase their personality in the cutest way possible. It's the ideal gift for a new baby, perfect for any occasion "
    "from baby showers to baby announcements. Celebrate the joy of a new life with this charming and meaningful baby bodysuit that will be cherished for years to come."
)
FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
STATUS_URL = "https://marketplace.walmartapis.com/v3/feeds/{}"

BULLETS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing, ensuring that your baby's outfit looks fantastic wash after wash.",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> Show your support for our heroes while dressing your little one in style with this adorable newborn romper from a veteran-owned small business.",
    "👶 <strong>Comfort and Convenience:</strong> Crafted from soft, breathable materials, this Bodysuit provides maximum comfort for your baby. Plus, the convenient snap closure makes diaper changes a breeze.",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> This funny Baby Bodysuit makes for an excellent baby shower gift or a thoughtful present for any new parents. It's a sweet and meaningful addition to any baby's wardrobe.",
    "📏 <strong>Versatile Sizing & Colors:</strong> Available in a range of sizes and colors, ensuring the perfect fit. Check our newborn outfit boy and girl sizing guide to find the right one for your little one."
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
    "12M White Short Sleeve": "12M White Short Sleeve"
}

# === FUNCTIONS ===
def get_token():
    try:
        res = requests.post(
            "https://marketplace.walmartapis.com/v3/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        res.raise_for_status()
        return res.json()["access_token"]
    except Exception as e:
        st.error(f"❌ Error getting access token: {e}")
        return None

def build_xml(df):
    try:
        required_cols = {"Title", "Handle", "Option1 Value", "Variant Price", "Variant Inventory Qty", "Image Src", "Image Position"}
        if not required_cols.issubset(df.columns):
            raise ValueError("Missing required columns in Shopify CSV.")

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
                    st.warning(f"⚠️ Variation not mapped: {raw}")
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
                ET.SubElement(item, "longDescription").text = STATIC_DESCRIPTION + "".join([f"<p>{b}</p>" for b in BULLETS])
                ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
                ET.SubElement(item, "variantGroupId").text = group_id
                ET.SubElement(item, "swatchImageUrl").text = main_image
                ET.SubElement(item, "IsPreorder").text = IS_PREORDER
                ET.SubElement(item, "productType").text = PRODUCT_TYPE
                inventory = ET.SubElement(item, "inventory")
                ET.SubElement(inventory, "quantity").text = str(qty)

        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
    except Exception as e:
        st.error(f"❌ XML generation failed: {e}")
        return None

def submit_feed(xml, token):
    try:
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
    except Exception as e:
        st.error(f"❌ Submission failed: {e}")
        return None

def track_feed(feed_id, token):
    try:
        res = requests.get(
            STATUS_URL.format(feed_id),
            headers={"Authorization": f"Bearer {token}", "WM_SVC.NAME": "Walmart Marketplace"}
        )
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.error(f"❌ Feed tracking failed: {e}")
        return None

# === STREAMLIT UI ===
st.set_page_config(page_title="Walmart Uploader", layout="wide")
st.title("🛒 Walmart Product Feed Uploader (All-in-One)")

uploaded = st.file_uploader("Upload Shopify products_export.csv", type="csv")
feed_status_id = st.text_input("Enter Feed ID to track status:")

if uploaded:
    try:
        df = pd.read_csv(uploaded)
        if st.button("🧠 Generate Walmart XML"):
            xml = build_xml(df)
            if xml:
                st.success("✅ XML Generated!")
                st.code(xml[:3000] + "...", language="xml")

                if st.button("📤 Submit to Walmart"):
                    token = get_token()
                    if token:
                        response = submit_feed(xml, token)
                        if response:
                            st.success("✅ Feed Submitted!")
                            st.code(response)
    except Exception as e:
        st.error(f"❌ Could not process CSV: {e}")

if feed_status_id:
    if st.button("🔍 Track Feed Status"):
        token = get_token()
        if token:
            result = track_feed(feed_status_id, token)
            if result:
                st.code(result)
