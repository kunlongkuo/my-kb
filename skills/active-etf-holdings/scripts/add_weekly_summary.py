#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute weekly additions and reductions using openpyxl directly (without pandas)."""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

EXCEL_PATH = Path("wiki/金融投資/主動型ETF持股明細.xlsx")
OUTPUT_SHEET_NAME = "Weekly Summary"
DETAIL_SHEET_NAME = "Weekly Additions"
REDUCTIONS_SHEET_NAME = "Weekly Reductions"

def parse_date(name: str):
    try:
        return datetime.strptime(name, "%Y%m%d")
    except Exception:
        return None

def load_date_sheets(wb):
    date_sheets = {}
    for name in wb.sheetnames:
        d = parse_date(name)
        if d:
            date_sheets[d] = name
    return date_sheets

def get_weekly_comparison_dates(date_sheets: dict, end_date_str: str = None):
    if not date_sheets:
        raise ValueError("No dated sheets found in the workbook.")
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y%m%d")
            if end_date not in date_sheets:
                valid_dates = [d for d in date_sheets if d <= end_date]
                if not valid_dates:
                    raise ValueError(f"No date sheets found on or before {end_date_str}")
                end_date = max(valid_dates)
        except Exception as e:
            raise ValueError(f"Invalid date format or date not found: {end_date_str}. Error: {e}")
    else:
        end_date = max(date_sheets.keys())
    
    monday = end_date - timedelta(days=end_date.weekday())
    last_week_start = monday - timedelta(days=7)
    last_week_end = monday - timedelta(days=3)
    
    last_week_dates = [d for d in date_sheets if last_week_start <= d <= last_week_end]
    
    if last_week_dates:
        start_date = max(last_week_dates)
    else:
        older_dates = [d for d in date_sheets if d < monday]
        if older_dates:
            start_date = max(older_dates)
        else:
            start_date = end_date
            
    return date_sheets[start_date], date_sheets[end_date]

def read_sheet_data(ws):
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    data = []
    for r in rows[1:]:
        if not r or r[0] is None:
            continue
        row_dict = {}
        for idx, val in enumerate(r):
            if idx < len(header):
                row_dict[header[idx]] = val
        data.append(row_dict)
    return data

def main():
    if not EXCEL_PATH.exists():
        print(f"Error: {EXCEL_PATH} not found.")
        return

    print(f"Loading workbook: {EXCEL_PATH}...")
    wb = load_workbook(EXCEL_PATH, data_only=True)
    date_sheets = load_date_sheets(wb)
    if not date_sheets:
        print("Error: No dated sheets found.")
        return

    start_name, end_name = get_weekly_comparison_dates(date_sheets)
    print(f"Comparing weekly sheets: {start_name} -> {end_name}")

    start_data = read_sheet_data(wb[start_name])
    end_data = read_sheet_data(wb[end_name])

    # Index start & end by (ETF代號, 持股代號)
    start_map = {}
    for r in start_data:
        key = (str(r.get("ETF代號", "")).strip(), str(r.get("持股代號", "")).strip())
        try:
            shares = int(float(r.get("持有張數", 0))) if r.get("持有張數") not in [None, "N/A"] else 0
        except ValueError:
            shares = 0
        try:
            ratio = float(r.get("投資比例(%)", 0)) if r.get("投資比例(%)") not in [None, "N/A"] else 0.0
        except ValueError:
            ratio = 0.0
        start_map[key] = {
            "etf_name": str(r.get("ETF名稱", "")).strip(),
            "stock_name": str(r.get("持股名稱", "")).strip(),
            "shares": shares,
            "ratio": ratio
        }

    end_map = {}
    for r in end_data:
        key = (str(r.get("ETF代號", "")).strip(), str(r.get("持股代號", "")).strip())
        try:
            shares = int(float(r.get("持有張數", 0))) if r.get("持有張數") not in [None, "N/A"] else 0
        except ValueError:
            shares = 0
        try:
            ratio = float(r.get("投資比例(%)", 0)) if r.get("投資比例(%)") not in [None, "N/A"] else 0.0
        except ValueError:
            ratio = 0.0
        end_map[key] = {
            "etf_name": str(r.get("ETF名稱", "")).strip(),
            "stock_name": str(r.get("持股名稱", "")).strip(),
            "shares": shares,
            "ratio": ratio
        }

    all_keys = set(start_map.keys()).union(set(end_map.keys()))

    summary_dict = {} # etf_id -> {etf_name, added_shares, reduced_shares}
    additions = []
    reductions = []

    for (etf_id, stock_id) in sorted(all_keys):
        s_info = start_map.get((etf_id, stock_id), {"shares": 0, "ratio": 0.0, "etf_name": "", "stock_name": ""})
        e_info = end_map.get((etf_id, stock_id), {"shares": 0, "ratio": 0.0, "etf_name": "", "stock_name": ""})

        etf_name = e_info["etf_name"] or s_info["etf_name"]
        stock_name = e_info["stock_name"] or s_info["stock_name"]

        s_shares = s_info["shares"]
        e_shares = e_info["shares"]
        s_ratio = s_info["ratio"]
        e_ratio = e_info["ratio"]

        diff_shares = e_shares - s_shares
        diff_ratio = round(e_ratio - s_ratio, 4)

        if etf_id not in summary_dict:
            summary_dict[etf_id] = {"etf_name": etf_name, "added_shares": 0, "reduced_shares": 0}

        if diff_shares > 0:
            summary_dict[etf_id]["added_shares"] += diff_shares
            additions.append({
                "ETF代號": etf_id,
                "ETF名稱": etf_name,
                "持股代號": stock_id,
                "持股名稱": stock_name,
                "總加碼張數": diff_shares,
                "週原比例": s_ratio,
                "加碼後比例": e_ratio,
                "差異": diff_ratio
            })
        elif diff_shares < 0:
            reduced_amount = -diff_shares
            summary_dict[etf_id]["reduced_shares"] += reduced_amount
            reductions.append({
                "ETF代號": etf_id,
                "ETF名稱": etf_name,
                "持股代號": stock_id,
                "持股名稱": stock_name,
                "總減碼張數": reduced_amount,
                "週原比例": s_ratio,
                "減碼後比例": e_ratio,
                "差異": diff_ratio
            })

    # Styles
    font_header = Font(name="Microsoft JhengHei", size=10, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    font_body = Font(name="Microsoft JhengHei", size=10)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    thin = Side(border_style="thin", color="D9D9D9")
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)

    # 1. Update Weekly Summary Sheet
    if OUTPUT_SHEET_NAME in wb.sheetnames:
        del wb[OUTPUT_SHEET_NAME]
    ws_summary = wb.create_sheet(title=OUTPUT_SHEET_NAME)

    summary_headers = ["ETF代號", "ETF名稱", "總加碼張數", "總減碼張數"]
    ws_summary.append(summary_headers)
    for col_idx, h in enumerate(summary_headers, start=1):
        cell = ws_summary.cell(row=1, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    for etf_id, s_data in sorted(summary_dict.items()):
        ws_summary.append([etf_id, s_data["etf_name"], s_data["added_shares"], s_data["reduced_shares"]])

    for row in ws_summary.iter_rows(min_row=2):
        for idx, cell in enumerate(row):
            cell.font = font_body
            cell.border = border_all
            if idx in [0, 1]:
                cell.alignment = align_left
            else:
                cell.alignment = align_right

    # 2. Update Weekly Additions Sheet
    if DETAIL_SHEET_NAME in wb.sheetnames:
        del wb[DETAIL_SHEET_NAME]
    ws_add = wb.create_sheet(title=DETAIL_SHEET_NAME)

    add_headers = ["ETF代號", "ETF名稱", "持股代號", "持股名稱", "總加碼張數", "週原比例", "加碼後比例", "差異"]
    ws_add.append(add_headers)
    for col_idx, h in enumerate(add_headers, start=1):
        cell = ws_add.cell(row=1, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    for item in additions:
        ws_add.append([
            item["ETF代號"], item["ETF名稱"], item["持股代號"], item["持股名稱"],
            item["總加碼張數"], item["週原比例"], item["加碼後比例"], item["差異"]
        ])

    for row in ws_add.iter_rows(min_row=2):
        for idx, cell in enumerate(row):
            cell.font = font_body
            cell.border = border_all
            if idx in [0, 1, 2, 3]:
                cell.alignment = align_left
            else:
                cell.alignment = align_right

    # 3. Update Weekly Reductions Sheet
    if REDUCTIONS_SHEET_NAME in wb.sheetnames:
        del wb[REDUCTIONS_SHEET_NAME]
    ws_red = wb.create_sheet(title=REDUCTIONS_SHEET_NAME)

    red_headers = ["ETF代號", "ETF名稱", "持股代號", "持股名稱", "總減碼張數", "週原比例", "減碼後比例", "差異"]
    ws_red.append(red_headers)
    for col_idx, h in enumerate(red_headers, start=1):
        cell = ws_red.cell(row=1, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    for item in reductions:
        ws_red.append([
            item["ETF代號"], item["ETF名稱"], item["持股代號"], item["持股名稱"],
            item["總減碼張數"], item["週原比例"], item["減碼後比例"], item["差異"]
        ])

    for row in ws_red.iter_rows(min_row=2):
        for idx, cell in enumerate(row):
            cell.font = font_body
            cell.border = border_all
            if idx in [0, 1, 2, 3]:
                cell.alignment = align_left
            else:
                cell.alignment = align_right

    print(f"Saving updated workbook to {EXCEL_PATH}...")
    wb.save(EXCEL_PATH)
    print("Successfully updated weekly summary sheets!")

if __name__ == "__main__":
    main()
