# Image Downloader for BOLD, iNaturalist, and TaiEOL

A simple Python script to download image datasets and their associated metadata from the Barcode of Life Data System (BOLD), iNaturalist, and the Taiwan Encyclopedia of Life (TaiEOL).

This script includes features to filter images by copyright license and saves all available metadata to ensure data traceability.

## ⚙️ Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Install Dependencies:**
    It is highly recommended to use a Python virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
    (Your `requirements.txt` should contain `pandas`, `requests`, and `tqdm`).

---

## 📥 Step 1: How to Get Your Inputs (Pre-processing)

Before running the script, you must gather the correct inputs for each data source.

### 1. BOLD (Barcode of Life)
This is the simplest. No pre-processing is needed.

* **Input:** A single taxon name (e.g., `"Scolytidae"`, `"Platypodinae"`).

### 2. iNaturalist
This requires you to **manually export a CSV from the iNaturalist website**. This exported CSV is your metadata file.

1.  Go to [iNaturalist.org](https://www.inaturalist.org/observations/export) and log in.
2.  In the main search bar, search for the taxon you want (e.g., "Scolytinae").
3.  Click the **"Filters"** tab (next to "Observations").
4.  In the "More Filters" pop-up, click the **"Download"** button.
5.  You will be taken to an export page. **This is the most important step:**
    * Click **"Edit columns"**.
    * Search for and add the **`license`** column. This is **required** if you want to filter by copyright.
    * Add any other columns you want in your metadata file (e.g., `taxon_subfamily_name`, `id`, `image_url` are recommended).
6.  Click **"Create Export"**.
7.  Wait for iNaturalist to generate the file. Download the file (e.g., `observations-12345.csv`) and place it in your repository folder.

* **Input:** The path to this downloaded `observations-12345.csv` file.

### 3. TaiEOL (Taiwan Encyclopedia of Life)
This requires two inputs: an API key and a species CSV file.

1.  **API Key:**
    * You must apply for an API key from the TaiEOL website (https://data.taieol.tw/content/api/v2).
2.  **Species CSV File:**
    * This script requires a CSV file that contains `genus` and `species` columns.
    * The `valid_species_names.csv` file included in this repository is the perfect input for this. You can also create your own.

* **Inputs:**
    1.  Your personal API key (a long string).
    2.  The path to your species CSV (e.g., `valid_species_names.csv`).

---

## 🚀 Step 2: How to Run the Script

Use the `download.py` script from your terminal. You must choose one of three commands: `bold`, `inat`, or `taieol`.

### `bold`

Downloads images and metadata from BOLD.

**Command:**
```bash
python download.py bold --taxon "YourTaxonName" [--out_dir "output_folder"]
```
* `--taxon` (Required): The name of the taxon to search for (e.g., `"Scolytidae"`).
* `--out_dir` (Optional): Directory to save images. (Default: `bold_images_<TaxonName>`)

### `inat`

Filters and downloads images using your iNaturalist CSV.

**Command:**
```bash
python download.py inat --csv "/path/to/metadata.csv" [--license "CC-BY" "CC-BY-NC"] [--out_dir "output_folder"]
```
* `--csv` (Required): Path to the `observations-12345.csv` file you downloaded from iNaturalist.
* `--license` (Optional): A space-separated list of allowed licenses. If omitted, downloads all images regardless of copyright.
* `--out_dir` (Optional): Directory to save images. (Default: `inat_images`)

### `taieol`

Downloads images and all metadata for a list of species.

**Command:**
```bash
python download.py taieol --api_key "YOUR_KEY" --species_csv "species.csv" [--license "CC-BY"] [--out_dir "output_folder"]
```
* `--api_key` (Required): Your personal TaiEOL API key.
* `--species_csv` (Required): Path to your CSV file with "genus" and "species" columns (e.g., `valid_species_names.csv`).
* `--license` (Optional): A space-separated list of allowed licenses. If omitted, downloads all images.
* `--out_dir` (Optional): Directory to save images. (Default: `taieol_images`)

---

## 📦 Step 3: Understanding Your Outputs (Images & Metadata)

The script organizes all outputs into the directory you specify (`--out_dir`).

* **`bold` Output:**
    * **Images:** A folder of `.jpg` images.
    * **Metadata:** A single **`<taxon>_metadata.xml`** file. This is the raw XML from BOLD containing all metadata for the downloaded records.

* **`inat` Output:**
    * **Images:** A folder of `.jpg` images.
    * **Metadata:** **Your input CSV file (`observations-12345.csv`) *is* the metadata file.** This file contains all the information (license, location, date, etc.) for the images you downloaded.

* **`taieol` Output:**
    * **Images:** A folder of `.jpg` images.
    * **Metadata:** A new **`taieol_metadata.csv`** file. This file is automatically created and contains **all** metadata (license, rights holder, descriptions, etc.) for every image that was downloaded.