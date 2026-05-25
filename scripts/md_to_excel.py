import pandas as pd
import re
import os

def parse_markdown_table(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the table part
    # A simple way is to look for lines starting and ending with |
    lines = content.split('\n')
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|'):
            # Skip separator lines like | :--- | :--- |
            if re.match(r'^\|\s*[:\-|\s]+\s*\|$', line.strip()):
                continue
            table_lines.append(line)
            in_table = True
        elif in_table:
            # Table ended
            if not line.strip():
                break
    
    if not table_lines:
        return None
    
    # Parse headers and rows
    headers = [h.strip() for h in table_lines[0].split('|') if h.strip()]
    rows = []
    for line in table_lines[1:]:
        row = [cell.strip() for cell in line.split('|') if cell.strip()]
        # Sometimes a trailing | leaves an empty cell if not careful, 
        # but the logic above handles it. 
        # Clean markdown formatting like ** or '
        clean_row = [re.sub(r'\*\*|\'', '', cell) for cell in row]
        if len(clean_row) == len(headers):
            rows.append(clean_row)
    
    return pd.DataFrame(rows, columns=headers)

files = {
    '主動型': 'i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md',
    '市值型': 'i:/Mark/my-kb/wiki/金融投資/市值型ETF清單.md',
    '高股息': 'i:/Mark/my-kb/wiki/金融投資/高股息ETF清單.md',
    '槓桿反向': 'i:/Mark/my-kb/wiki/金融投資/槓桿反向型ETF清單.md',
    '海外型': 'i:/Mark/my-kb/wiki/金融投資/海外型ETF清單.md'
}

output_file = 'i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, file_path in files.items():
        df = parse_markdown_table(file_path)
        if df is not None:
            df.to_sheet = writer # This is not how you do it with ExcelWriter
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Auto-adjust column width (optional but nice)
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65+idx)].width = max_len

print(f"Excel file created at: {output_file}")
