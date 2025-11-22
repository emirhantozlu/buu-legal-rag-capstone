# src/preprocessing/text_cleaner.py

import re
from typing import List
from .pdf_loader import PageText


def normalize_whitespace(text: str) -> str:
    """
    Fazla boşlukları, tab karakterlerini vs. normalize eder.

    Örnek:
        - Birden fazla boşluğu tek boşluğa indirir.
        - Satır sonu + boşluk kombinasyonlarını sadeleştirir.
    """
    # Tab'leri boşluğa çevir
    text = text.replace("\t", " ")
    # Birden fazla boşluğu tek boşluğa indir
    text = re.sub(r"[ ]{2,}", " ", text)
    # Fazla boş satırları azalt (3+ satır sonunu 2 satıra indir)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def merge_broken_lines(text: str) -> str:
    """
    PDF'ten gelen ve her satırda kırılmış cümleleri birleştirmeye çalışır.

    Genel fikir:
        - Satır sonunda nokta, iki nokta, soru işareti vb. yoksa
          ve bir sonraki satır küçük harfle başlıyorsa satır sonunu boşluk yap.
    """
    lines = text.splitlines()
    merged_lines: List[str] = []
    buffer = ""

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Boş satır gördüysek buffer'ı push et
            if buffer:
                merged_lines.append(buffer)
                buffer = ""
            merged_lines.append("")  # boş satır korunsun
            continue

        if not buffer:
            buffer = stripped
            continue

        # Önceki satır son karakter
        last_char = buffer[-1] if buffer else ""
        first_char = stripped[0]

        # Eğer önceki satır noktalama ile bitmiyorsa ve
        # yeni satır küçük harfle / sayı ile başlıyorsa birleştir
        if last_char not in ".:;?!)" and first_char.islower():
            buffer = buffer + " " + stripped
        else:
            merged_lines.append(buffer)
            buffer = stripped

    if buffer:
        merged_lines.append(buffer)

    return "\n".join(merged_lines)


def fix_hyphenation(text: str) -> str:
    """
    Satır sonlarında tire ile veya mantıksız şekilde bölünmüş kelimeleri birleştirir.

    Örnek:
        'öğrenim gören öğ-\nrenciler' -> 'öğrenim gören öğrenciler'
        'sın\navları' -> 'sınavları'
    """
    # 1) Satır sonu + tire + yeni satır: 'öğ-\nrenciler' -> 'öğrenciler'
    pattern_hyphen = r"(\w+)-\n(\w+)"
    text = re.sub(pattern_hyphen, r"\1\2", text)

    # 2) Çok kısa bir kelime satır sonunda bölünmüşse: 'sın\nav' -> 'sınav'
    # Burada ilk parça 1-3 karakter; ikinci parça kelime ile devam ediyor.
    pattern_short_break = r"(\b\w{1,3})\n(\w+)"
    text = re.sub(pattern_short_break, r"\1\2", text)

    return text



def clean_page_text(page: PageText) -> PageText:
    """
    Tek bir sayfanın metnini temizler (boşluk, satır sonu, tire).

    Args:
        page: PageText nesnesi.

    Returns:
        Yeni PageText (aynı page_number, temizlenmiş text).
    """
    text = page.text
    text = fix_hyphenation(text)
    text = merge_broken_lines(text)
    text = normalize_whitespace(text)
    return PageText(page_number=page.page_number, text=text)


def clean_document_pages(pages: List[PageText]) -> List[PageText]:
    """
    Tüm sayfalar için temizleme işlemini uygular.
    """
    return [clean_page_text(p) for p in pages]


def clean_document_as_single_text(pages: List[PageText]) -> str:
    """
    Tüm sayfaları temizleyip tek bir metin halinde döner.
    """
    cleaned_pages = clean_document_pages(pages)
    full_text = "\n".join(p.text for p in cleaned_pages)
    return full_text
