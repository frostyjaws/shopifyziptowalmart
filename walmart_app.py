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
GTIN_PLACEHOLDER = "000000000000"  # GTIN exemption placeholder
IS_PREORDER = "No"

STATIC_DESCRIPTION = (
    "<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, "
    "the perfect baby shower gift that will be cherished for years to come. This charming piece "
    "of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether "
    "it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby bodysuit "
    "is sure to delight.</p>"
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

# === MASTER VARIATIONS & PRICES (static mapping) ===
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

# Force all items to show as in-stock quantity = 999
INVENTORY_FOR_ALL = 999

def get_token():
    """Retrieve OAuth token from Walmart."""
    try:
        res = requests.post(
            "https://marketplace.walmartapis.com/v3/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        st.error(f"❌ Error getting access token: {e}")
        return None

def build_xml(df):
    """
    Build a Walmart‐compliant ItemFeed XML string from a Shopify DataFrame,
    using the fixed_variations mapping regardless of what Shopify sends.
    """
    try:
        # Required columns (case‐sensitive)
        required_cols = {
            "Title", "Handle",
            "Variant Inventory Qty", "Image Src", "Image Position"
        }
        if not required_cols.issubset(df.columns):
            raise ValueError("Missing one or more required columns in the CSV.")

        ns = "http://walmart.com/"
        ET.register_namespace("", ns)
        root = ET.Element(f"{{{ns}}}ItemFeed")

        for handle, group in df.groupby("Handle"):
            title = group["Title"].iloc[0]
            # Build your “smart” productName
            display_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

            # Use the first non‐null “Image Src” for this handle
            images = (
                group[["Image Src", "Image Position"]]
                .dropna()
                .sort_values(by="Image Position")
            )
            if images.empty:
                continue

            main_image = images.iloc[0]["Image Src"]
            group_id = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]

            for variation_name, variation_price in fixed_variations.items():
                size = color = sleeve = ""
                parts = variation_name.split(" ", 2)
                if len(parts) == 3:
                    size, color, sleeve = parts
                elif len(parts) == 2:
                    size, color = parts
                elif len(parts) == 1:
                    size = parts[0]

                short_handle = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]
                sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

                item = ET.SubElement(root, "Item")
                ET.SubElement(item, "sku").text = sku
                ET.SubElement(item, "productName").text = display_title
                ET.SubElement(item, "productIdType").text = "GTIN"
                ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
                ET.SubElement(item, "manufacturerPartNumber").text = sku
                ET.SubElement(item, "price").text = f"{variation_price:.2f}"
                ET.SubElement(item, "brand").text = BRAND

                # Main image
                ET.SubElement(item, "mainImageUrl").text = main_image

                # Up to five additionalImageUrl tags (no numeric suffix)
                for img_url in IMAGES[:5]:
                    ET.SubElement(item, "additionalImageUrl").text = img_url

                # Long description (static + bullets)
                full_desc = STATIC_DESCRIPTION + "".join(f"<p>{b}</p>" for b in BULLETS)
                ET.SubElement(item, "longDescription").text = full_desc

                ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
                ET.SubElement(item, "variantGroupId").text = group_id
                ET.SubElement(item, "swatchImageUrl").text = main_image
                ET.SubElement(item, "isPreorder").text = IS_PREORDER

                # Exact Category / Subcategory / ProductType (per screenshot)
                ET.SubElement(item, "category").text = "Fashion"
                ET.SubElement(item, "subCategory").text = "Baby Garments & Accessories"
                ET.SubElement(item, "productType").text = "Baby Bodysuits & One‐Pieces"

                # Force inventory to 999
                inventory = ET.SubElement(item, "inventory")
                ET.SubElement(inventory, "quantity").text = str(INVENTORY_FOR_ALL)

        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    except Exception as e:
        st.error(f"❌ XML generation failed: {e}")
        return None

def submit_feed(xml: str, token: str) -> str:
    """
    Submit the generated XML to Walmart API; return the raw response text.
    """
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

def track_feed(feed_id: str, token: str) -> str:
    """
    Check the status of a previously submitted feed ID.
    """
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
st.set_page_config(page_title="Walmart Product Feed Uploader", layout="wide")
st.title("🛒 Walmart Product Feed Uploader (Fixed Variations)")

# Initialize session_state for generated XML
if "generated_xml" not in st.session_state:
    st.session_state.generated_xml = None
if "xml_filename" not in st.session_state:
    st.session_state.xml_filename = None

uploaded = st.file_uploader(
    "Upload your Shopify products_export.csv",
    type="csv",
    help=(
        "Make sure your CSV has the following headers (case‐sensitive):\n"
        "  • Title\n"
        "  • Handle\n"
        "  • Variant Inventory Qty\n"
        "  • Image Src\n"
        "  • Image Position"
    )
)

feed_status_id = st.text_input(
    "Enter Feed ID to track status:",
    placeholder="e.g. 1234567890"
)

if uploaded:
    try:
        df = pd.read_csv(uploaded)

        # Show detected columns and a small preview for debugging
        st.write("▶️ Detected columns:", list(df.columns))
        st.write(df.head(2))

        # Generate XML and store in session_state
        if st.button("🧠 Generate Walmart XML"):
            xml_str = build_xml(df)
            if xml_str:
                # Save to a timestamped file for download
                filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(xml_str)

                st.session_state.generated_xml = xml_str
                st.session_state.xml_filename = filename

                st.success("✅ XML Generated!")
                st.code(xml_str[:3000] + "...", language="xml")

        # If we already have generated XML, show Download + Submit buttons
        if st.session_state.generated_xml:
            # Download button
            with open(st.session_state.xml_filename, "rb") as f_bin:
                st.download_button(
                    "📥 Download XML",
                    data=f_bin,
                    file_name=st.session_state.xml_filename,
                    mime="application/xml",
                )

            # Submit button (uses the same XML from session_state)
            if st.button("📤 Submit to Walmart"):
                token = get_token()
                if token:
                    response = submit_feed(st.session_state.generated_xml, token)
                    if response:
                        st.success("✅ Feed Submitted!")
                        st.code(response)

    except Exception as e:
        st.error(f"❌ Could not process CSV: {e}")

# Track Feed Status
if feed_status_id:
    if st.button("🔍 Track Feed Status"):
        token = get_token()
        if token:
            result = track_feed(feed_status_id, token)
            if result:
                st.code(result)
