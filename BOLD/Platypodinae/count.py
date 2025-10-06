import xml.etree.ElementTree as ET


#to verify total count
root = ET.parse("bold_metadata.xml").getroot()
records = root.findall(".//record")
images = root.findall(".//image_file")

print(f"Total records: {len(records)}")
print(f"Total image URLs: {len(images)}")


