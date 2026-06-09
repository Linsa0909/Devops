"""
Document Parser — 提取上传文件中的文本 (参考 PaddleOCR 思路)
支持: .md / .txt / .docx / .pdf / .html / .png / .jpg
图片通过 DeepSeek Vision API 提取文字 (PaddleOCR 同类功能)
"""
from __future__ import annotations
import os
import base64
from pathlib import Path
from typing import Optional


class DocumentParser:
    """多格式文档解析器 — 将文件转为结构化文本"""

    SUPPORTED = {".md", ".txt", ".docx", ".pdf", ".html", ".htm", ".png", ".jpg", ".jpeg"}

    def __init__(self, llm_service=None):
        self.llm = llm_service  # 用于图片 OCR

    def parse(self, filepath: str) -> dict:
        """
        解析文件，返回: {"text": "...", "type": "markdown|plain|cv_ocr", "filename": "...", "size": 0}
        """
        path = Path(filepath)
        ext = path.suffix.lower()
        filename = path.name
        size = path.stat().st_size

        if ext not in self.SUPPORTED:
            return {"text": f"[不支持的文件类型: {ext}]", "type": "unsupported", "filename": filename, "size": size}

        text = ""

        # ── 纯文本类 ──
        if ext in (".md", ".txt"):
            text = path.read_text(encoding="utf-8", errors="replace")
            return {"text": text, "type": "markdown" if ext == ".md" else "plain", "filename": filename, "size": size}

        # ── HTML ──
        if ext in (".html", ".htm"):
            try:
                from html.parser import HTMLParser
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                    def handle_data(self, data):
                        self.text.append(data.strip())
                extractor = TextExtractor()
                extractor.feed(path.read_text(encoding="utf-8", errors="replace"))
                text = "\n".join(t for t in extractor.text if t)
            except:
                text = path.read_text(encoding="utf-8", errors="replace")
            return {"text": text, "type": "html", "filename": filename, "size": size}

        # ── DOCX ──
        if ext == ".docx":
            text = self._parse_docx(path)
            return {"text": text, "type": "docx", "filename": filename, "size": size}

        # ── PDF ──
        if ext == ".pdf":
            text = self._parse_pdf(path)
            return {"text": text, "type": "pdf", "filename": filename, "size": size}

        # ── 图片 (OCR via DeepSeek Vision) ──
        if ext in (".png", ".jpg", ".jpeg"):
            text = self._ocr_image(path)
            return {"text": text, "type": "cv_ocr", "filename": filename, "size": size}

        return {"text": "[解析失败]", "type": "error", "filename": filename, "size": size}

    def parse_and_append_to_description(self, filepath: str, existing_desc: str) -> str:
        """解析文件内容并追加到需求描述"""
        result = self.parse(filepath)
        text = result.get("text", "")
        if not text or text.startswith("["):
            return existing_desc

        # 格式化追加
        section = f"\n\n## 📎 上传文档: {result['filename']} ({result['type']})\n\n{text[:3000]}"
        return existing_desc + section

    # ── 私有解析器 ──

    def _parse_docx(self, path: Path) -> str:
        """python-docx 提取文本"""
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            return "[需安装 python-docx: pip install python-docx]"
        except Exception as e:
            return f"[DOCX解析失败: {e}]"

    def _parse_pdf(self, path: Path) -> str:
        """PyPDF2 提取文本"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
            return "\n\n".join(pages)
        except ImportError:
            return "[需安装 PyPDF2: pip install PyPDF2]"
        except Exception as e:
            return f"[PDF解析失败: {e}]"

    def _ocr_image(self, path: Path) -> str:
        """图片 OCR — 使用 DeepSeek Vision API (等价于 PaddleOCR 功能)"""
        if not self.llm:
            return "[OCR 不可用: LLM 服务未初始化]"

        try:
            # 读取图片并 base64
            with open(path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()

            ext = path.suffix.lower().replace(".", "")
            mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
            mime = mime_map.get(ext, "image/png")

            # 调用 DeepSeek Vision (复用现有 LLM 客户端)
            import httpx
            client = httpx.Client(timeout=60)
            resp = client.post(
                f"{self.llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.llm.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请提取这张图片中的所有文字内容。只输出文字，不要任何解释或格式。"},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}},
                        ]
                    }],
                    "max_tokens": 2000,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[OCR 失败: {e}]"
