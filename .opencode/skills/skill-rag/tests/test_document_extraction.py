import sys
import dataclasses
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

try:
    import pymupdf
except ImportError:  # optional test-only PDF fixture generator
    pymupdf = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skill_rag


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class FakePage:
    def __init__(self, text: str):
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakePdfReader:
    is_encrypted = False
    pages = [FakePage("PDF marker from page one"), FakePage("")]


class DocumentExtractionTests(unittest.TestCase):
    def test_sql_literal_preserves_windows_path_backslashes(self):
        value = "I:\\Mark\\my-kb\\wiki\\烘培食譜\\鳳梨酥.md"

        self.assertEqual(
            skill_rag.sql_literal(value),
            "'I:\\\\Mark\\\\my-kb\\\\wiki\\\\烘培食譜\\\\鳳梨酥.md'",
        )

    def test_docx_paragraphs_and_table_text_are_indexed(self):
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <w:document xmlns:w="{WORD_NS}"><w:body>
          <w:p><w:r><w:t>DOCX heading</w:t></w:r></w:p>
          <w:tbl><w:tr><w:tc><w:p><w:r><w:t>docxmarker table content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
          <w:sectPr/>
        </w:body></w:document>'''

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = root / "sources"
            sources.mkdir()
            with zipfile.ZipFile(sources / "guide.docx", "w") as archive:
                archive.writestr("word/document.xml", xml)
            (sources / "manual.pdf").write_bytes(b"mock pdf")

            setup = {
                "rag": {"chunk_size": 1200, "chunk_overlap": 150},
                "openai": {},
            }
            with patch.object(skill_rag, "PdfReader", return_value=FakePdfReader()):
                records = skill_rag.build_chunks(root, setup)

        by_type = {record.doc_type: record for record in records}
        self.assertIn("docxmarker table content", by_type["docx"].content)
        self.assertIn("PDF marker from page one", by_type["pdf"].content)
        self.assertIn("Page 1", by_type["pdf"].content)

    @unittest.skipIf(pymupdf is None or skill_rag.PdfReader is None, "PDF fixture dependencies are unavailable")
    def test_real_pdf_selectable_text_is_extracted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "selectable.pdf"
            document = pymupdf.open()
            page = document.new_page()
            page.insert_text((72, 72), "pdfmarker extracted from real PDF")
            document.save(path)
            document.close()

            text = skill_rag.read_text(path)

        self.assertIn("pdfmarker extracted from real PDF", text)
        self.assertIn("Page 1", text)

    def test_pdf_requires_pypdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manual.pdf"
            path.write_bytes(b"mock pdf")
            with patch.object(skill_rag, "PdfReader", None):
                with self.assertRaisesRegex(RuntimeError, "requires pypdf"):
                    skill_rag.read_text(path)

    def test_scanned_pdf_without_extractable_text_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scan.pdf"
            path.write_bytes(b"mock pdf")
            with patch.object(skill_rag, "PdfReader", return_value=type("Reader", (), {"is_encrypted": False, "pages": [FakePage("")]})()):
                with self.assertRaisesRegex(ValueError, "OCR first"):
                    skill_rag.read_text(path)

    def test_local_image_uses_sidecar_text_and_renders_clickable_file_link(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = root / "sources"
            sources.mkdir()
            (sources / "blueprint.png").write_bytes(b"image bytes")
            (sources / "blueprint.md").write_text("Architecture diagram for bird habitat", encoding="utf-8")
            setup = {"rag": {"chunk_size": 1200, "chunk_overlap": 150}, "openai": {}}

            records = skill_rag.build_chunks(root, setup)
            payload = {"records": [dataclasses.asdict(record) for record in records]}
            hits = skill_rag.query_index(payload, "bird habitat")
            answer = skill_rag.render_answer("bird habitat", hits)

        image_record = next(record for record in records if record.doc_type == "image")
        self.assertIn("Architecture diagram for bird habitat", image_record.content)
        self.assertIn("blueprint.png", answer)
        self.assertIn("file:///", answer)

    def test_video_transcript_and_markdown_media_urls_are_rendered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = root / "sources"
            sources.mkdir()
            (sources / "installation.mp4").write_bytes(b"video bytes")
            (sources / "installation.vtt").write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nConnect the sensor cable\n",
                encoding="utf-8",
            )
            (sources / "guide.md").write_text(
                "# Sensor setup\n\n![Wiring diagram](https://cdn.example.test/wiring.png)\n\n"
                "[Demo video](https://youtu.be/demo123)\n\n"
                "[Cloud video](https://drive.google.com/file/d/clip-id/view)\n\n"
                "![Local photo](installation.mp4)",
                encoding="utf-8",
            )
            setup = {"rag": {"chunk_size": 1200, "chunk_overlap": 150}, "openai": {}}

            records = skill_rag.build_chunks(root, setup)
            video_record = next(record for record in records if record.doc_type == "video")
            self.assertIn("Connect the sensor cable", video_record.content)

            payload = {"records": [dataclasses.asdict(record) for record in records]}
            hits = skill_rag.query_index(payload, "sensor wiring demo")
            answer = skill_rag.render_answer("sensor wiring demo", hits)

        self.assertIn("https://cdn.example.test/wiring.png", answer)
        self.assertIn("https://youtu.be/demo123", answer)
        self.assertIn("https://drive.google.com/file/d/clip-id/view", answer)
        self.assertIn("file:///", answer)


if __name__ == "__main__":
    unittest.main()
