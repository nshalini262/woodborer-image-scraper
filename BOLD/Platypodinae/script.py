import os
import requests
import xml.etree.ElementTree as ET

def get_bold_metadata(taxon="Platypodinae", save_file = 'bold_metadata.xml'):
    # public API url
    url = "http://v3.boldsystems.org/index.php/API_Public/specimen"
    # checking for platypodinae subfamily
    params = {
        "taxon": taxon,
        "format": "xml"
    }

    # api call
    response = requests.get(url, params=params)
    response.raise_for_status()

    with open(save_file, "wb") as f:
        f.write(response.content)
    
    root = ET.fromstring(response.content)
    
    return root
    

def download_images(root, out_dir="bold_images"):
    os.makedirs(out_dir, exist_ok=True)
    count = 0

    for record in root.findall(".//record"):
        processid = record.findtext("processid", default="unknown")

        media = record.find("specimen_imagery")
        if media is not None:
            for m in media.findall("media"):
                image_url = m.findtext("image_file")
                if not image_url:
                    continue
                try:
                    img_data = requests.get(image_url).content
                    file_name = f"{processid}_{count}.jpg"
                    file_path = os.path.join(out_dir, file_name)

                    with open(file_path, "wb") as f:
                        f.write(img_data)

                    print(f"Downloaded: {file_name}")
                    count += 1
                except Exception as e:
                    print(f"Error downloading {image_url}: {e}")


if __name__ == "__main__":
    metadata = get_bold_metadata()
    download_images(metadata)

