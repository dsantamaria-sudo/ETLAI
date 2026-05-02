import pandas as pd

# Read the Excel file without assuming a header
df_raw = pd.read_excel("C:/Users/Usuario/Downloads/example.xlsx", header=None)
print(f"Shape: {df_raw.shape}")
print("\nFirst 10 rows:")
for i, row in df_raw.head(10).iterrows():
    print(f"Row {i}: {list(row)}")