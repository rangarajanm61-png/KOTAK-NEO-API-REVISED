import pandas as pd
import glob

files = glob.glob("*scrip*.csv") + glob.glob("*Scrip*.csv") + glob.glob("*master*.csv") + glob.glob("*Master*.csv")

print("CSV files found:")
for f in files:
    print(f)

for f in files:
    try:
        df = pd.read_csv(f)
        print("\nFILE:", f)
        print(df.columns.tolist())

        mask = df.astype(str).apply(
            lambda col: col.str.contains("NIFTY", case=False, na=False)
        ).any(axis=1)

        result = df[mask]
        print(result.head(30).to_string())
    except Exception as e:
        print("Error reading", f, e)