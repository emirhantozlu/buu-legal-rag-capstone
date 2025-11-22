# src/preprocessing/chunker.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re

from .pdf_loader import PageText
from .text_cleaner import clean_document_as_single_text


@dataclass
class ArticleBlock:
    """
    Tek bir MADDE bloğunu temsil eder (ham metin).
    """
    article_no: str          # "MADDE 44" gibi
    start_index: int         # full_text içindeki başlangıç index'i
    end_index: int           # full_text içindeki bitiş index'i
    text: str                # madde metni (başlık + içerik)


@dataclass
class Chunk:
    """
    Embedding ve FAISS için kullanılacak temel chunk yapısı.
    Akademik tarafta da bu yapıyı kullanacağız.
    """
    id: str
    doc_id: str
    doc_type: str            # "kanun" veya "yönetmelik"
    doc_name: str            # insan okunabilir belge adı
    article_no: str          # "MADDE 44" gibi
    paragraph_no: Optional[str]  # "(1)", "(2-3)" vb. yoksa None
    section_title: Optional[str] # bölüm başlığı; yoksa None
    text: str                # asıl chunk metni

def extract_section_title_and_body(article_text: str) -> (Optional[str], str):
    """
    Madde metninin içindeki olası bölüm başlığını (örn. 'Kapsam', 'Tanımlar')
    tespit etmeye çalışır.

    Basit heuristik:
        - Metni satır satır böler.
        - 'MADDE' ile başlayan satırdan sonra gelen,
          tek satırlık, içinde nokta/dizgi işareti olmayan,
          çok uzun olmayan (örn. < 40 karakter) bir satırı
          'section_title' olarak kabul eder.

    section_title bulunamazsa None döner, metnin tamamı body olarak kalır.
    """
    lines = article_text.splitlines()
    if not lines:
        return None, article_text

    # İlk satır genellikle 'MADDE X – ...'
    new_lines = []
    section_title = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i == 0:
            # İlk satırı olduğu gibi ekle
            new_lines.append(lines[i])
            i += 1
            continue

        # Eğer henüz section_title bulunmamışsa ve bu satır başlık kriterini sağlıyorsa
        if section_title is None:
            # Çok uzun değil, içinde nokta, iki nokta vb. yok, parantezle başlamıyor
            if (0 < len(line) <= 40
                    and all(ch not in line for ch in [".", ":", ";"])
                    and not line.startswith("(")):
                section_title = line
                # Bu satırı body'ye eklemiyoruz; sadece metadata olarak alıyoruz
                i += 1
                continue

        # Normal satır
        new_lines.append(lines[i])
        i += 1

    cleaned_text = "\n".join(new_lines).strip()
    return section_title, cleaned_text



def split_text_into_articles(full_text: str) -> List[ArticleBlock]:
    """
    Temizlenmiş tüm belge metnini MADDE bazlı bloklara böler.

    Varsayım: 'MADDE 1 -', 'MADDE 2 -' gibi bir pattern var.

    Returns:
        ArticleBlock listesi.
    """
    # MADDE veya Madde ile başlayan satırlar
    pattern = re.compile(r"(MADDE|Madde)\s+(\d+)\s*[-–]", re.MULTILINE)

    matches = list(pattern.finditer(full_text))
    articles: List[ArticleBlock] = []

    for i, match in enumerate(matches):
        start = match.start()
        # Son madde ise sonuna kadar; değilse bir sonraki MADDE'nin başına kadar
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        article_text = full_text[start:end].strip()
        article_no = f"MADDE {match.group(2)}"
        articles.append(ArticleBlock(
            article_no=article_no,
            start_index=start,
            end_index=end,
            text=article_text
        ))

    return articles


def split_article_into_chunks(article: ArticleBlock,
                              doc_id: str,
                              doc_type: str,
                              doc_name: str,
                              max_chars: int = 1500,
                              short_threshold: int = 600) -> List[Chunk]:
    """
    Tek bir MADDE bloğunu 0, 1 veya daha fazla chunk'e böler.

    Strateji:
        - Önce olası section_title'ı ayıkla.
        - Eğer madde metni kısa/orta ise tek chunk yap.
        - Eğer çok uzunsa paragraf/fıkra bazlı böl.
    """
    # Önce olası bölüm başlığını ayır
    section_title, body_text = extract_section_title_and_body(article.text)

    # Basit uzunluk kontrollü: kısa/orta ise tek chunk
    if len(body_text) <= max_chars:
        chunk_id = f"{doc_id}_{article.article_no.replace(' ', '').lower()}"
        return [Chunk(
            id=chunk_id,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            article_no=article.article_no,
            paragraph_no=None,
            section_title=section_title,   # artık dolu olabilir
            text=body_text
        )]

    # Çok uzun maddeler için numaralı fıkralara göre split
    paragraph_pattern = re.compile(r"\(\d+\)")
    parts = paragraph_pattern.split(body_text)
    markers = paragraph_pattern.findall(body_text)

    chunks: List[Chunk] = []
    buffer = ""
    current_paragraphs: List[str] = []

    # parts[0] genelde madde başlığı / giriş; onu buffer'a alıyoruz
    buffer += parts[0]

    for part, marker in zip(parts[1:], markers):
        candidate = marker + part

        if len(buffer) + len(candidate) <= max_chars:
            buffer += "\n" + candidate
            current_paragraphs.append(marker)
        else:
            paragraph_no = "-".join(current_paragraphs) if current_paragraphs else None
            chunk_id = f"{doc_id}_{article.article_no.replace(' ', '').lower()}_{len(chunks)+1}"
            chunks.append(Chunk(
                id=chunk_id,
                doc_id=doc_id,
                doc_type=doc_type,
                doc_name=doc_name,
                article_no=article.article_no,
                paragraph_no=paragraph_no,
                section_title=section_title if len(chunks) == 0 else None,
                text=buffer.strip()
            ))
            buffer = candidate
            current_paragraphs = [marker]

    if buffer.strip():
        paragraph_no = "-".join(current_paragraphs) if current_paragraphs else None
        chunk_id = f"{doc_id}_{article.article_no.replace(' ', '').lower()}_{len(chunks)+1}"
        chunks.append(Chunk(
            id=chunk_id,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            article_no=article.article_no,
            paragraph_no=paragraph_no,
            section_title=section_title if len(chunks) == 0 else None,
            text=buffer.strip()
        ))

    return chunks



def build_chunks_from_pdf_pages(pages: List[PageText],
                                doc_id: str,
                                doc_type: str,
                                doc_name: str) -> List[Chunk]:
    """
    PDF sayfalarından MADDE bazlı chunk listesi üretir.

    Akış:
        1) Sayfa metinlerini temizle
        2) Tüm belgeyi tek metin haline getir
        3) MADDE'lere böl
        4) Her MADDE'yi chunk'lara böl
    """
    full_text = clean_document_as_single_text(pages)
    article_blocks = split_text_into_articles(full_text)

    all_chunks: List[Chunk] = []
    for article in article_blocks:
        article_chunks = split_article_into_chunks(
            article=article,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name
        )
        all_chunks.extend(article_chunks)

    return all_chunks


def chunks_to_dicts(chunks: List[Chunk]) -> List[Dict[str, Any]]:
    """
    Chunk dataclass'lerini JSON-friendly dict formuna çevirir.
    """
    return [
        {
            "id": c.id,
            "doc_id": c.doc_id,
            "doc_type": c.doc_type,
            "doc_name": c.doc_name,
            "article_no": c.article_no,
            "paragraph_no": c.paragraph_no,
            "section_title": c.section_title,
            "text": c.text,
        }
        for c in chunks
    ]
