import csv
import random
import xml.etree.ElementTree as ET
from datetime import datetime

# ----- Static configuration -----
INVENTORY_QUANTITY = 999
ADDITIONAL_IMAGE_URLS = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_39118440-7324-4737-a9b6-9bc4e9dab73d.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_32129b22-54df-4f68-8da7-30b93a0e85cc.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_07aeb493-bfd6-40d8-809d-709037313156.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/1a38365ed663e060d2590b04a0ec16b00004fe45_f8aaa5cc-0182-4bf8-9ada-860c6d175f25.jpg?v=1740931622",
]

PRICE_MAP = {
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
    "6M Natural Short Sleeve": 31.99,
}

def generate_sku(title, variation):
    base = ''.join(c for c in title if c.isalnum())
    color = next((c for c in ["White", "Pink", "Blue", "Natural"] if c in variation), "Unknown")
    size = next((s for s in ["Newborn", "0-3M", "3-6M", "6-9M", "6M"] if s in variation), "Unknown")
    sleeve = "Long" if "Long" in variation else "Short"
    rand = str(random.randint(100, 999))
    return f"{base}-{color}-{size}-{sleeve}-{rand}"

def get_price(variation):
    return PRICE_MAP.get(variation.strip(), 27.99)

def build_walmart_xml(csv_file):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"walmart_feed_{now}.xml"

    tree = ET.Element("WalmartFeed")
    items_el = ET.SubElement(tree, "ItemList")

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Title", "").strip()
            variation = row.get("Variant Title", "").strip()
            main_image = row.get("Image Src", "").strip()

            sku = generate_sku(title, variation)
            price = get_price(variation)

            item_el = ET.SubElement(items_el, "Item")
            ET.SubElement(item_el, "sku").text = sku
            ET.SubElement(item_el, "productName").text = f"{title} - Baby Bodysuit"
            ET.SubElement(item_el, "productId").text = "EXEMPT"
            ET.SubElement(item_el, "productIdType").text = "GTIN"
            ET.SubElement(item_el, "price").text = f"{price:.2f}"
            ET.SubElement(item_el, "quantity").text = str(INVENTORY_QUANTITY)
            ET.SubElement(item_el, "mainImageUrl").text = main_image

            for i, url in enumerate(ADDITIONAL_IMAGE_URLS, start=1):
                ET.SubElement(item_el, f"additionalImageUrl{i}").text = url

    tree_bytes = ET.tostring(tree, encoding='utf-8', method='xml')
    with open(output_filename, "wb") as f:
        f.write(tree_bytes)
    print(f"✅ Walmart XML generated: {output_filename}")

# Run the generator on your CSV
build_walmart_xml("products_export.csv")
