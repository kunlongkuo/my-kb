"""上傳時送給 YouTube 的 snippet（只用標準庫，yt_upload.py 一匯入就要 Google 的套件，抽出來才測得到）。"""


def upload_snippet(title, description, tags, category, language):
    """tags 是逗號分隔的字串，空的去掉；language 是影片的預設語言（例 zh-Hant、en）。"""
    return {"title": title, "description": description, "tags": [t for t in tags.split(",") if t],
            "categoryId": category, "defaultLanguage": language}
