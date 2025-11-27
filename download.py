import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Helper Function ---

def download_image(url, file_path):
    """Helper function to download a single image."""
    try:
        img_data = requests.get(url, timeout=10).content
        if not img_data:
            return url, "Downloaded file is empty"
        
        with open(file_path, "wb") as f:
            f.write(img_data)
        return file_path, None
    except Exception as e:
        return url, e

# --- BOLD (Barcode of Life Data) Downloader ---

def get_bold_metadata(taxon, save_file):
    """Fetches BOLD metadata for a specific taxon and saves it to an XML file."""
    url = "http://v3.boldsystems.org/index.php/API_Public/specimen"
    params = {"taxon": taxon, "format": "xml"}
    
    print(f"[INFO] Requesting BOLD metadata for taxon: {taxon}...")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed for {taxon}: {e}")
        return None

    # Save the raw XML metadata
    with open(save_file, "wb") as f:
        f.write(response.content)
    
    print(f"[INFO] Metadata saved to {save_file}")
    
    try:
        root = ET.fromstring(response.content)
        return root
    except ET.ParseError as e:
        print(f"[ERROR] Failed to parse XML metadata: {e}")
        return None

def download_bold_images(root, out_dir):
    """Parses XML and downloads all BOLD images in parallel."""
    print(f"[INFO] Searching for images in metadata...")
    image_jobs = []
    
    for record in root.findall(".//record"):
        processid = record.findtext("processid", default="unknown")
        media = record.find("specimen_imagery")
        if media is not None:
            for idx, m in enumerate(media.findall("media")):
                image_url = m.findtext("image_file")
                if not image_url:
                    continue
                
                file_name = f"{processid}_{idx}.jpg"
                file_path = os.path.join(out_dir, file_name)
                image_jobs.append((image_url, file_path))

    if not image_jobs:
        print("[INFO] No image URLs found in the metadata.")
        return

    print(f"[INFO] Found {len(image_jobs)} images. Starting download...")
    log_file = os.path.join(out_dir, "download_log.txt")
    
    with open(log_file, "w") as log, ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(download_image, url, path): (url, path) for url, path in image_jobs}
        
        for future in tqdm(as_completed(future_to_url), total=len(image_jobs), desc="Downloading BOLD Images"):
            url, path = future_to_url[future]
            file_path, error = future.result()
            
            if error:
                log.write(f"Error downloading {url}: {error}\n")
            else:
                log.write(f"Downloaded: {os.path.basename(file_path)}\n")

    print(f"[INFO] BOLD download complete. Log saved to {log_file}")

def run_bold_download(args):
    """Main function for BOLD download."""
    taxon_name = args.taxon
    if args.out_dir == f"bold_images_{taxon_name}":
        out_dir = args.out_dir
    else:
        out_dir = args.out_dir if args.out_dir else f"bold_images_{taxon_name}"
        
    os.makedirs(out_dir, exist_ok=True)
    # This is the metadata output for BOLD
    xml_file = os.path.join(out_dir, f"{taxon_name}_metadata.xml")
    
    metadata_root = get_bold_metadata(taxon_name, xml_file)
    
    if metadata_root is not None:
        download_bold_images(metadata_root, out_dir)

# --- iNaturalist Downloader ---

def run_inat_download(args):
    """Main function for iNaturalist download with license filtering."""
    csv_file = args.csv
    out_dir = args.out_dir
    allowed_licenses = args.license
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        df = pd.read_csv(csv_file)
        df.columns = [c.strip() for c in df.columns]
    except FileNotFoundError:
        print(f"[ERROR] Metadata CSV not found at: {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Could not read CSV: {e}")
        sys.exit(1)

    # --- License Filtering ---
    if allowed_licenses:
        if 'license' not in df.columns:
            print("[ERROR] '--license' flag was used, but no 'license' column found in the CSV.")
            print("[INFO] Please re-export from iNaturalist and include the 'license' column.")
            print(f"[INFO] Found columns: {df.columns.tolist()}")
            sys.exit(1)
        
        print(f"[INFO] Original record count: {len(df)}")
        df = df[df['license'].isin(allowed_licenses)]
        print(f"[INFO] Filtered to {len(df)} records based on {allowed_licenses}")

    if df.empty:
        print("[INFO] No records remaining after filtering. Exiting.")
        return

    print(f"[INFO] Preparing {len(df)} records from iNaturalist CSV...")
    image_jobs = []
    required_cols = ['image_url', 'taxon_subfamily_name', 'id']
    if not all(col in df.columns for col in required_cols):
        print(f"[ERROR] CSV must contain columns: {required_cols}")
        print(f"[INFO] Found columns: {df.columns.tolist()}")
        sys.exit(1)

    for _, row in df.iterrows():
        url = row['image_url']
        if pd.isna(url):
            continue
        
        # Get original, full-resolution image
        url = url.replace('square', 'original').replace('medium', 'original').replace('large', 'original')
        
        taxon_name = str(row['taxon_subfamily_name']).replace(' ', '_')
        image_id = row['id']
        filename = f"{taxon_name}_{image_id}.jpg"
        file_path = os.path.join(out_dir, filename)
        image_jobs.append((url, file_path))

    if not image_jobs:
        print("[INFO] No images found to download.")
        return

    print(f"[INFO] Starting download of {len(image_jobs)} images...")
    log_file = os.path.join(out_dir, "inat_download_log.txt")
    
    with open(log_file, "w") as log, ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(download_image, url, path): (url, path) for url, path in image_jobs}
        
        for future in tqdm(as_completed(future_to_url), total=len(image_jobs), desc="Downloading iNat Images"):
            url, path = future_to_url[future]
            file_path, error = future.result()
            
            if error:
                log.write(f"Error downloading {url}: {error}\n")
            else:
                log.write(f"Downloaded: {os.path.basename(file_path)}\n")

    print(f"[INFO] iNaturalist download complete. Log saved to {log_file}")

# --- TaiEOL (Taiwan Encyclopedia of Life) Downloader ---

def search_taieol_media(species_name, api_key):
    """Searches the TaiEOL API for a single species and returns a list of media objects (dicts)."""
    base_url = "https://data.taieol.tw/api/v2/taieol_object/tid/full"
    params = {"token": api_key, "scientificName": species_name}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except:
        return []

    media_items = []
    if not data:
        return []
        
    if isinstance(data, dict):
        data = [data] 
        
    try:
        for species_result in data:
            if 'media' in species_result:
                media_items.extend(species_result['media'])
    except Exception as e:
        print(f"[WARN] Error parsing data for {species_name}: {e}")
        pass
        
    return media_items

def run_taieol_download(args):
    """Main function for TaiEOL download with license filtering and metadata export."""
    api_key = args.api_key
    species_csv = args.species_csv
    out_dir = args.out_dir
    allowed_licenses = args.license
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        df = pd.read_csv(species_csv)
        if 'genus' not in df.columns or 'species' not in df.columns:
            print(f"[ERROR] CSV file '{species_csv}' must contain 'genus' and 'species' columns.")
            sys.exit(1)
        
        df['species_clean'] = df['species'].apply(lambda x: str(x).strip().split()[-1] if pd.notna(x) else x)
        
        df['full_name'] = df['genus'] + ' ' + df['species_clean']
        species_list = df['full_name'].dropna().unique().tolist()
        
    except FileNotFoundError:
        print(f"[ERROR] Species CSV file not found at: {species_csv}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to read species CSV: {e}")
        sys.exit(1)

    print(f"[INFO] Found {len(species_list)} unique species names in {species_csv}.")
    
    log_file = os.path.join(out_dir, "taieol_download_log.txt")
    image_jobs = []
    metadata_records = []
    
    print("[INFO] Searching TaiEOL API for all species and filtering...")
    for species_name in tqdm(species_list, desc="Searching API"):
        media_items = search_taieol_media(species_name, api_key)
        
        if not media_items:
            with open(log_file, "a") as log:
                log.write(f"No images found for: {species_name}\n")
            continue
        
        for idx, item in enumerate(media_items):
            # --- License Filtering ---
            license_str = item.get('license', 'Unknown')
            if allowed_licenses and license_str not in allowed_licenses:
                continue # Skip this image, license doesn't match
                
            url = item.get('baseUrl', item.get('url'))
            if not url:
                continue
                
            clean_species_name = species_name.replace(' ', '_').replace('.', '')
            file_name = f"{clean_species_name}_{idx}.jpg"
            file_path = os.path.join(out_dir, file_name)
            
            image_jobs.append((url, file_path))
            
            # --- Save ALL metadata for this item ---
            item_metadata = item.copy()
            item_metadata['download_filename'] = file_name
            item_metadata['query_species_name'] = species_name
            metadata_records.append(item_metadata)

    if not image_jobs:
        print("[INFO] No images found for any species matching the license criteria.")
        return

    # --- Save Metadata CSV ---
    metadata_df = pd.DataFrame(metadata_records)
    metadata_csv_path = os.path.join(out_dir, "taieol_metadata.csv")
    try:
        metadata_df.to_csv(metadata_csv_path, index=False)
        print(f"[INFO] Saved ALL metadata for {len(metadata_df)} images to {metadata_csv_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata CSV: {e}")

    # --- Download all images that passed the filter ---
    print(f"[INFO] Found {len(image_jobs)} total images matching filters. Starting download...")
    
    with open(log_file, "a") as log, ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(download_image, url, path): (url, path) for url, path in image_jobs}
        
        for future in tqdm(as_completed(future_to_url), total=len(image_jobs), desc="Downloading TaiEOL Images"):
            url, path = future_to_url[future]
            file_path, error = future.result()
            
            if error:
                log.write(f"Error downloading {url}: {error}\n")
            else:
                log.write(f"Downloaded: {os.path.basename(file_path)}\n")

    print(f"[INFO] TaiEOL download complete. Log saved to {log_file}")

# --- MAIN SCRIPT LOGIC ---

def main():
    parser = argparse.ArgumentParser(
        description="Image Downloader for BOLD, iNaturalist, and TaiEOL.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='source', required=True,
                                       help="The data source to download from: 'bold', 'inat', or 'taieol'")
    
    # --- BOLD Sub-parser ---
    bold_parser = subparsers.add_parser('bold', help='Download from BOLD (Barcode of Life Data System)')
    bold_parser.add_argument(
        '--taxon', type=str, required=True, 
        help='The scientific taxon name to download (e.g., "Scolytinae")')
    bold_parser.add_argument(
        '--out_dir', type=str, default=None,
        help='Output directory. (Default: bold_images_<taxon>)')
    bold_parser.set_defaults(func=run_bold_download, out_dir=None)

    # --- iNaturalist Sub-parser ---
    inat_parser = subparsers.add_parser('inat', help='Download from iNaturalist using a metadata CSV')
    inat_parser.add_argument(
        '--csv', type=str, required=True, 
        help='Path to the iNaturalist metadata CSV file')
    inat_parser.add_argument(
        '--out_dir', type=str, default='inat_images', 
        help='Output directory. (Default: inat_images)')
    inat_parser.add_argument(
        '--license', nargs='+', default=None,
        help='(Optional) A list of allowed licenses. e.g., --license "CC-BY" "CC-BY-NC"')
    inat_parser.set_defaults(func=run_inat_download)

    # --- TaiEOL Sub-parser ---
    taieol_parser = subparsers.add_parser('taieol', help='Download from TaiEOL (Taiwan Encyclopedia of Life) using an API key')
    taieol_parser.add_argument(
        '--api_key', type=str, required=True, 
        help='Your personal API key for the TaiEOL API.')
    taieol_parser.add_argument(
        '--species_csv', type=str, required=True,
        help='A .csv file with "genus" and "species" columns (e.g., valid_species_names.csv)')
    taieol_parser.add_argument(
        '--out_dir', type=str, default='taieol_images', 
        help='Output directory. (Default: taieol_images)')
    taieol_parser.add_argument(
        '--license', nargs='+', default=None,
        help='(Optional) A list of allowed licenses. e.g., --license "CC-BY" "CC-BY-NC"')
    taieol_parser.set_defaults(func=run_taieol_download)

    args = parser.parse_args()
    
    if args.source == 'bold' and args.out_dir is None:
        args.out_dir = f"bold_images_{args.taxon}"
    
    if hasattr(args, 'license') and args.license:
        print(f"[INFO] Filtering for licenses: {args.license}")

    args.func(args)

if __name__ == "__main__":
    main()