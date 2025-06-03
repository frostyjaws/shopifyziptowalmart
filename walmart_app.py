def build_xml(df):
    """
    Build a Walmart‐compliant ItemFeed XML string from a Shopify DataFrame.

    - Always produces at least one <Item> per Handle.
    - Correctly falls back to “Price / United States” if “Variant Price” is missing or NaN.
    """
    try:
        # Make sure the CSV has these seven headers (case-sensitive):
        required_cols = {
            "Title", "Handle",
            "Option1 Value", "Variant Price",
            "Variant Inventory Qty", "Image Src", "Image Position"
        }
        if not required_cols.issubset(df.columns):
            raise ValueError("Missing one or more required columns in the CSV.")

        # Prepare XML root with Walmart namespace
        ns = "http://walmart.com/"
        ET.register_namespace("", ns)
        root = ET.Element("{%s}ItemFeed" % ns)

        # Group by Handle → each group = one product (with possible variants)
        for handle, group in df.groupby("Handle"):
            title = group["Title"].iloc[0]
            display_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

            # Grab images, sorted by “Image Position”
            images = (
                group[["Image Src", "Image Position"]]
                .dropna()
                .sort_values(by="Image Position")
            )
            if images.empty:
                # Skip if no images at all (Walmart requires at least one image per Item)
                continue

            main_image = images.iloc[0]["Image Src"]
            group_id = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]

            # Iterate each row (variant) under this handle
            for _, row in group.iterrows():
                raw_variant = str(row.get("Option1 Value", "")).strip()

                # If blank or “Default Title,” treat as single-variant fallback
                if raw_variant == "" or raw_variant == "Default Title":
                    mapped = "Default Title"
                else:
                    mapped = VARIATIONS.get(raw_variant)
                    if mapped is None:
                        st.warning(f"⚠️ Variation not mapped: '{raw_variant}' — using raw text as fallback.")
                        mapped = raw_variant

                # Split “mapped” string into size/color/sleeve
                size = color = sleeve = ""
                parts = mapped.split(" ", 2)
                if len(parts) == 3:
                    size, color, sleeve = parts
                elif len(parts) == 2:
                    size, color = parts
                    sleeve = ""
                elif len(parts) == 1:
                    size = parts[0]
                    color = ""
                    sleeve = ""
                # else: all remain empty

                # 1) Try “Variant Price”:
                raw_price = row.get("Variant Price", "")
                try:
                    price_val = float(raw_price)
                except:
                    price_val = 0.0

                # If Variant Price is zero or NaN, fall back to “Price / United States”:
                if price_val <= 0 or str(raw_price).lower() == "nan":
                    # Shopify sometimes puts the real per-country price under "Price / United States"
                    if "Price / United States" in row:
                        try:
                            price_val = float(row.get("Price / United States", 0))
                        except:
                            price_val = 0.0
                    else:
                        price_val = 0.0

                # (Optional) Further fallback: “Variant Compare At Price” if you want to use that instead:
                if price_val <= 0 and "Variant Compare At Price" in row:
                    try:
                        price_val = float(row.get("Variant Compare At Price", 0))
                    except:
                        price_val = 0.0

                # If price_val is still zero, you can either skip this item or leave it at 0.00.
                # For now, we'll issue a warning and continue with price=0.00:
                if price_val <= 0:
                    st.warning(f"⚠️ Zero price for SKU (Handle='{handle}', Option='{raw_variant}'), setting price=0.00.")

                # Inventory quantity:
                try:
                    qty = int(float(row.get("Variant Inventory Qty", 0)))
                except:
                    qty = 0

                short_handle = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]
                sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

                # Build the <Item> node
                item = ET.SubElement(root, "Item")
                ET.SubElement(item, "sku").text = sku
                ET.SubElement(item, "productName").text = display_title
                ET.SubElement(item, "productIdType").text = "GTIN"
                ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
                ET.SubElement(item, "manufacturerPartNumber").text = sku
                ET.SubElement(item, "price").text = f"{price_val:.2f}"
                ET.SubElement(item, "brand").text = BRAND
                ET.SubElement(item, "mainImageUrl").text = main_image

                # Add up to 5 additional images
                for idx, img_url in enumerate(IMAGES):
                    ET.SubElement(item, f"additionalImageUrl{idx+1}").text = img_url

                # Full longDescription (static + bullet points)
                full_desc = STATIC_DESCRIPTION + "".join(f"<p>{b}</p>" for b in BULLETS)
                ET.SubElement(item, "longDescription").text = full_desc

                ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
                ET.SubElement(item, "variantGroupId").text = group_id
                ET.SubElement(item, "swatchImageUrl").text = main_image
                ET.SubElement(item, "isPreorder").text = IS_PREORDER
                ET.SubElement(item, "productType").text = PRODUCT_TYPE

                # Always include <inventory><quantity>
                inventory = ET.SubElement(item, "inventory")
                ET.SubElement(inventory, "quantity").text = str(qty)

        # Serialize the entire <ItemFeed> to a UTF-8 string
        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    except Exception as e:
        st.error(f"❌ XML generation failed: {e}")
        return None
