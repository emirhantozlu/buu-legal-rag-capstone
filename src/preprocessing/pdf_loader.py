# src/preprocessing/pdf_loader.py

from dataclasses import dataclass
from typing import List
import pdfplumber
import pathlib


@dataclass
class PageText:
    """
    Tek bir PDF sayfasından çıkarılan metin bilgisini tutar.
    """
    page_number: int
    text: str


def load_pdf_pages(pdf_path: str) -> List[PageText]:
    """
    Verilen PDF dosyasından sayfa bazlı ham metin çıkarır.

    Args:
        pdf_path: PDF dosyasının yolu (relative veya absolute).

    Returns:
        PageText nesnelerinden oluşan bir liste.
    """
    pdf_file = pathlib.Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF bulunamadı: {pdf_file}")

    pages: List[PageText] = []

    with pdfplumber.open(str(pdf_file)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=i, text=text))

    return pages


def load_pdf_as_single_text(pdf_path: str, separator: str = "\n") -> str:
    """
    PDF'in tüm sayfalarını tek bir büyük metin halinde birleştirir.

    Args:
        pdf_path: PDF yolu.
        separator: Sayfalar arasında kullanılacak ayraç (default: satır sonu).

    Returns:
        Tüm PDF metni (ham, temizlenmemiş).
    """
    pages = load_pdf_pages(pdf_path)
    joined_text = separator.join(page.text for page in pages)
    return joined_text


def debug_save_pages_to_txt(pages: List[PageText], output_path: str) -> None:
    """
    Geliştirme sırasında PDF'ten gelen ham sayfa metinlerini
    incelemek için basit bir .txt çıktısı üretir.

    Args:
        pages: PageText listesi.
        output_path: Kaydedilecek .txt dosyasının yolu.
    """
    out_file = pathlib.Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with out_file.open("w", encoding="utf-8") as f:
        for p in pages:
            f.write(f"===== PAGE {p.page_number} =====\n")
            f.write(p.text)
            f.write("\n\n")
