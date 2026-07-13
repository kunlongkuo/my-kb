import os
import zipfile
import re
import xml.etree.ElementTree as ET
import posixpath
import sys

# Reconfigure stdout to use utf-8 to print Chinese sheet names correctly on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

excel_path = "I:/Mark/my-kb/raw/圖片提示詞/生圖提示詞範例.xlsx"
output_dir = "I:/Mark/my-kb/raw/assets/圖片提示詞"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Namespace dictionary for openxml files
ns = {
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

def clean_filename(filename):
    # Remove characters that are illegal in Windows/Linux file names
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def extract_images():
    print(f"Opening Excel archive: {excel_path}...")
    
    if not os.path.exists(excel_path):
        print(f"Error: {excel_path} does not exist!")
        return

    extracted_count = 0
    sheet_image_map = {}

    with zipfile.ZipFile(excel_path) as z:
        # 1. Map sheet name to sheet XML file path
        wb_xml = z.read("xl/workbook.xml")
        wb_root = ET.fromstring(wb_xml)
        
        # Read workbook relationships to resolve sheet paths
        wb_rels_xml = z.read("xl/_rels/workbook.xml.rels")
        rels_root = ET.fromstring(wb_rels_xml)
        wb_rels = {}
        for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            wb_rels[rel.attrib['Id']] = rel.attrib['Target']
            
        sheets = {}
        for s in wb_root.findall('.//main:sheet', ns):
            name = s.attrib['name']
            rId = s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target_path = wb_rels[rId]
            sheets[name] = f"xl/{target_path}"
            
        print(f"Found {len(sheets)} sheets.")

        # 2. For each sheet, trace drawings and extract images
        for sheet_name, sheet_path in sheets.items():
            sheet_xml = z.read(sheet_path)
            sheet_root = ET.fromstring(sheet_xml)
            
            # Find the drawing element inside the sheet
            drawing_elem = sheet_root.find('.//main:drawing', ns)
            if drawing_elem is None:
                continue
                
            drawing_rId = drawing_elem.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            
            # Resolve drawing path via sheet relationships
            sheet_dir, sheet_file = posixpath.split(sheet_path)
            sheet_rels_path = f"{sheet_dir}/_rels/{sheet_file}.rels"
            
            if sheet_rels_path not in z.namelist():
                continue
                
            sheet_rels_xml = z.read(sheet_rels_path)
            sheet_rels_root = ET.fromstring(sheet_rels_xml)
            sheet_rels = {}
            for rel in sheet_rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                sheet_rels[rel.attrib['Id']] = rel.attrib['Target']
                
            drawing_target = sheet_rels.get(drawing_rId)
            if not drawing_target:
                continue
                
            drawing_path = posixpath.normpath(posixpath.join(sheet_dir, drawing_target))
            
            # Read drawing XML and relationships
            if drawing_path not in z.namelist():
                continue
                
            drawing_xml = z.read(drawing_path)
            drawing_root = ET.fromstring(drawing_xml)
            
            drawing_dir, drawing_file = posixpath.split(drawing_path)
            drawing_rels_path = f"{drawing_dir}/_rels/{drawing_file}.rels"
            
            if drawing_rels_path not in z.namelist():
                continue
                
            drawing_rels_xml = z.read(drawing_rels_path)
            drawing_rels_root = ET.fromstring(drawing_rels_xml)
            drawing_rels = {}
            for rel in drawing_rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                drawing_rels[rel.attrib['Id']] = rel.attrib['Target']
                
            # Find all pictures (pic elements) inside drawing
            pics = drawing_root.findall('.//xdr:pic', ns)
            if not pics:
                continue
                
            sheet_images = []
            
            for idx, pic in enumerate(pics):
                blip = pic.find('.//a:blip', ns)
                if blip is None:
                    continue
                    
                embed_rId = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if not embed_rId:
                    continue
                    
                img_target = drawing_rels.get(embed_rId)
                if not img_target:
                    continue
                    
                img_zip_path = posixpath.normpath(posixpath.join(drawing_dir, img_target))
                
                # Read image binary
                try:
                    img_data = z.read(img_zip_path)
                    ext = posixpath.splitext(img_zip_path)[1]
                    
                    # Safe destination file name
                    cleaned_name = clean_filename(sheet_name)
                    # If multiple images, use _1, _2... otherwise just the sheet name
                    suffix = f"_{idx+1}" if len(pics) > 1 else ""
                    dest_file_name = f"{cleaned_name}{suffix}{ext}"
                    dest_path = os.path.join(output_dir, dest_file_name)
                    
                    # Write to destination
                    with open(dest_path, "wb") as f_out:
                        f_out.write(img_data)
                        
                    sheet_images.append(dest_file_name)
                    extracted_count += 1
                except Exception as e:
                    print(f"  Error extracting image from {sheet_name} ({img_zip_path}): {e}")
                    
            if sheet_images:
                sheet_image_map[sheet_name] = sheet_images
                print(f"Extracted {len(sheet_images)} images for sheet: {sheet_name}")
                
    print(f"\nSuccessfully extracted total of {extracted_count} images to {output_dir}")
    
    # Save the mapping to a JSON file for metadata/referencing
    import json
    mapping_path = os.path.join(output_dir, "image_mapping.json")
    with open(mapping_path, "w", encoding="utf-8") as f_map:
        json.dump(sheet_image_map, f_map, ensure_ascii=False, indent=2)
    print(f"Saved mapping data to {mapping_path}")

if __name__ == "__main__":
    extract_images()
