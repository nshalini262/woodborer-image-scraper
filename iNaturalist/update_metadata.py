import pandas as pd

csv_path = "/home/nannapanenis/blue-hulcr/nannapanenis/beetle_images/iNat/metadata_files/all_bark_beetles_inaturalist_filtered_13Oct2025.csv"
output_csv = csv_path  # overwrite 


df = pd.read_csv(csv_path)
df.columns = [c.strip() for c in df.columns]  # clean column names



df['file_name'] = df.apply(lambda row: f"{row['taxon_subfamily_name']}_{row['id']}.jpg", axis=1)


cols = ['file_name'] + [c for c in df.columns if c != 'file_name']
df = df[cols]

df.to_csv(output_csv, index=False)

print(f"Updated CSV saved with file_name as first column: {output_csv}")
print(f"Total rows: {len(df)}")
