
import pandas as pd
import xml.etree.ElementTree as ET
import re
import random

# === SETTINGS ===
SHOPIFY_CSV_PATH = "products_export.csv"

# === STATIC VALUES ===
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"

# === STATIC DESCRIPTIONS ===
STATIC_DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby bodysuit is sure to delight.</p>
<p>Our Custom Baby Bodysuit features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby bodysuit is designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.</p>
<p>Perfect for both baby boys and girls, this versatile baby bodysuit is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps make changing a breeze, providing convenience for busy parents.</p>
<p>Whether you're looking for a personalized baby bodysuit, a funny baby bodysuit, or a cute baby bodysuit, this Custom Baby Bodysuit has it all. It’s ideal for celebrating the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.</p>
<p>Imagine gifting this delightful baby bodysuit at a baby shower or using it as a memorable baby announcement or pregnancy reveal. It’s perfect for anyone searching for a unique baby gift, announcement baby bodysuit, or a special new baby bodysuit. This baby bodysuit is not just an item of clothing; it’s a keepsake that celebrates the joy and wonder of a new life.</p>
<p>From baby boy clothes to baby girl clothes, this baby bodysuit is perfect for any newborn. Whether it’s a boho design, a Fathers Day gift, or custom baby clothes, this piece is a wonderful addition to any baby's wardrobe.</p>
<p>Get this Custom Baby Bodysuit today and let your little one showcase their personality in the cutest way possible. It's the ideal gift for a new baby, perfect for any occasion from baby showers to baby announcements. Celebrate the joy of a new life with this charming and meaningful baby bodysuit that will be cherished for years to come.</p>
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

# === VARIATION MAP FROM SHOPIFY `Option1 Value` ===
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

    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

if __name__ == "__main__":
    shopify_df = pd.read_csv(SHOPIFY_CSV_PATH)
    shopify_df = shopify_df.dropna(subset=["Handle"])
    xml_output = build_walmart_xml(shopify_df)
    with open("walmart_product_feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_output)
    print("✅ XML feed generated: walmart_product_feed.xml")
