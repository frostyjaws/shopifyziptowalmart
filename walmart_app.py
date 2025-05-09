if uploaded_file:
    df = pd.read_csv(uploaded_file, low_memory=False)
    df = df.dropna(subset=['Handle'])
    grouped = df.groupby('Handle')

    zip_buffer = BytesIO()
    batch_index = 1
    xlsx_rows = []

    def save_batch_to_zip(batch_rows, batch_index, zipf):
        temp_df = pd.DataFrame(batch_rows)
        batch_xlsx = BytesIO()
        with pd.ExcelWriter(batch_xlsx, engine='openpyxl') as writer:
            temp_df.to_excel(writer, index=False)
        zipf.writestr(f"products_batch_{batch_index}.xlsx", batch_xlsx.getvalue())

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for index, (handle, group) in enumerate(grouped):
            title = group['Title'].iloc[0]
            smart_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

            images = group[['Image Src', 'Image Position']].dropna().sort_values(by='Image Position')
            if images.empty:
                continue

            main_image = images.iloc[0]['Image Src']
            random_suffix = str(random.randint(100, 999))
            short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
            parent_sku = f"{short_handle}-Parent-{random_suffix}"

            parent_row = {
                'SKU': parent_sku,
                'Product Name': smart_title,
                'Description': static_description,
                'Brand': 'NOFO VIBES',
                'Price': '',
                'Main Image URL': '',
                'Other Image URL1': '',
                'Other Image URL2': '',
                'Other Image URL3': '',
                'Other Image URL4': '',
                'Other Image URL5': '',
                'Parent SKU': '',
                'Relationship Type': '',
                'Variation Theme': 'Size-Color-Sleeve',
                'Material': 'Cotton',
                'Fabric Content': '100% Cotton',
                'Country of Origin': 'Imported',
                'Gender': 'Unisex',
                'Age Group': 'Infant',
                'Manufacturer Part Number': parent_sku,
                'Fulfillment Lag Time': 2,
                'Product Tax Code': '2038710'
            }
            parent_row.update(key_features)
            new_rows = [parent_row]

            for variation, fixed_price in fixed_variations.items():
                parts = variation.split()
                if len(parts) < 3:
                    continue
                size = parts[0]
                color = parts[1]
                sleeve = ' '.join(parts[2:])
                sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random_suffix}"
                child_row = {
                    'SKU': sku,
                    'Product Name': smart_title,
                    'Description': static_description,
                    'Brand': 'NOFO VIBES',
                    'Price': fixed_price,
                    'Main Image URL': main_image,
                    'Other Image URL1': forced_accessory_images[0],
                    'Other Image URL2': forced_accessory_images[1],
                    'Other Image URL3': forced_accessory_images[2],
                    'Other Image URL4': forced_accessory_images[3],
                    'Other Image URL5': forced_accessory_images[4],
                    'Parent SKU': parent_sku,
                    'Relationship Type': 'variation',
                    'Variation Theme': 'Size-Color-Sleeve',
                    'Material': 'Cotton',
                    'Fabric Content': '100% Cotton',
                    'Country of Origin': 'Imported',
                    'Gender': 'Unisex',
                    'Age Group': 'Infant',
                    'Manufacturer Part Number': sku,
                    'Fulfillment Lag Time': 2,
                    'Product Tax Code': '2038710'
                }
                child_row.update(key_features)
                new_rows.append(child_row)

            test_buffer = BytesIO()
            with pd.ExcelWriter(test_buffer, engine='openpyxl') as writer:
                pd.DataFrame(xlsx_rows + new_rows).to_excel(writer, index=False)

            if test_buffer.tell() > 4.9 * 1024 * 1024:
                save_batch_to_zip(xlsx_rows, batch_index, zipf)
                batch_index += 1
                xlsx_rows = new_rows
            else:
                xlsx_rows.extend(new_rows)

        if xlsx_rows:
            save_batch_to_zip(xlsx_rows, batch_index, zipf)

    st.success("Walmart XLSX files generated successfully.")
    st.download_button(
        label="Download Walmart Upload ZIP (.xlsx files)",
        data=zip_buffer.getvalue(),
        file_name="walmart_upload_ready.zip",
        mime="application/zip"
    )
