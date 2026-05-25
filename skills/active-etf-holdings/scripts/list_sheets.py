import pandas as pd, json
path = r'i:/Mark/my-kb/wiki/金融投資/主動型ETF持股明細.xlsx'
xl = pd.ExcelFile(path)
print(json.dumps(xl.sheet_names, ensure_ascii=False))
