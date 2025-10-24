import os
import requests
import xml.etree.ElementTree as ET

def get_bold_metadata(taxon="Scolytinae", save_file='bold_metadata2.xml'):
    """
    Downloads BOLD metadata for the given taxon and parses XML robustly.
    """
    url = "http://v3.boldsystems.org/index.php/API_Public/specimen"
    params = {"taxon": taxon, "format": "xml"}

    print(f"Requesting metadata for taxon: {taxon}")
    response = requests.get(url, params=params)
    response.raise_for_status()


    with open(save_file, "wb") as f:
        f.write(response.content)
    print(f"Metadata saved to {save_file}")

 
    with open(save_file, "r", encoding="utf-8", errors="ignore") as f:
        xml_data = f.read()

    root = ET.fromstring(xml_data)
    print(f"XML parsed successfully for {taxon}")
    return root


def download_images(root, out_dir="bold_images2", log_file="download_log.txt"):
    """
    Downloads specimen images from BOLD XML metadata.
    Logs all downloads and errors to a file to prevent flooding SLURM output.
    """
    os.makedirs(out_dir, exist_ok=True)
    count = 0

    with open(log_file, "w") as log:
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

                        log.write(f"Downloaded: {file_name}\n")
                        count += 1
                    except Exception as e:
                        log.write(f"Error downloading {image_url}: {e}\n")

    print(f"Finished downloading images. Log saved to {log_file}")


if __name__ == "__main__":
    metadata = get_bold_metadata()
    download_images(metadata)
