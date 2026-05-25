import pandas as pd
import sys

EXCEL_PATH = r'i:/Mark/my-kb/wiki/金融投資/主動型ETF持股明細.xlsx'
SHEET_NAME = 'Weekly Additions'

def main():
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # Ensure there are at least 7 columns (0-indexed G=6, F=5)
        if df.shape[1] < 7:
            print(f'Error: Sheet "{SHEET_NAME}" has {df.shape[1]} columns, need at least 7 to compute G-F.')
            sys.exit(1)
        # Compute 差異 as column G - column F
        # Use column positions; assuming columns are ordered.
        df['差異'] = df.iloc[:, 6] - df.iloc[:, 5]
        # Write back to same sheet, replacing it
        with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        print('Successfully added 差異 column to Weekly Additions.')
    except Exception as e:
        print('Failed:', e)
        sys.exit(1)

if __name__ == '__main__':
    main()
