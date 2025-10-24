import os
import pandas as pd
import requests

csv_file = "/blue/hulcr/nannapanenis/beetle_images/iNat/metadata_files/all_bark_beetles_inaturalist_filtered_13Oct2025.csv"
out_dir = "inat_images"          
log_file = "inat_download_log.txt"  


os.makedirs(out_dir, exist_ok=True)


df = pd.read_csv(csv_file)


print("Columns in CSV:", df.columns.tolist())

images = []
for idx, row in df.iterrows():
    url = row['image_url']  
    taxon_name = str(row['taxon_subfamily_name']).replace(' ', '_')  
    filename = f"{taxon_name}_{idx}.jpg"
    images.append((url, filename))

print(f"Found {len(images)} images to download.")


with open(log_file, "w") as log:
    for url, filename in images:
        try:
            img_data = requests.get(url, timeout=10).content
            with open(os.path.join(out_dir, filename), "wb") as f:
                f.write(img_data)
            log.write(f"Downloaded: {filename}\n")
        except Exception as e:
            log.write(f"Error downloading {url}: {e}\n")

print(f"Finished downloading images. Log saved to {log_file}")
