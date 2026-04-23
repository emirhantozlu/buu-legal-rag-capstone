# src/preprocessing/chunker.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re

from src.config import resolve_chunking_params

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
    section_title: Optional[str] = None  # Öncesindeki kısa başlık (örn. "Amaç")


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


@dataclass(frozen=True)
class ChunkingParams:
    """Doc-type veya dış input'a göre chunk oluşturma stratejisini tanımlar."""

    max_chars: int = 1500
    propagate_section_title: bool = False
    chunk_overlap_chars: int = 0
    prepend_metadata_header: bool = False
    force_single_chunk: bool = False

    @classmethod
    def for_doc_type(cls, doc_type: str) -> "ChunkingParams":
        config_values = resolve_chunking_params(doc_type)
        return cls(
            max_chars=config_values.get("max_chars", 1500),
            propagate_section_title=config_values.get("propagate_section_title", False),
            chunk_overlap_chars=config_values.get("chunk_overlap_chars", 0),
            prepend_metadata_header=config_values.get("prepend_metadata_header", False),
            force_single_chunk=config_values.get("force_single_chunk", False),
        )


def _section_title_for_chunk(section_title: Optional[str],
                             propagate: bool,
                             chunk_index: int) -> Optional[str]:
    """Chunk sırasına göre section_title bilgisini hangi chunk'a taşıyacağımızı belirler."""
    if not section_title:
        return None
    if propagate or chunk_index == 0:
        return section_title
    return None


def _build_chunk_text(body_text: str,
                      article_no: str,
                      section_title: Optional[str],
                      prepend_metadata_header: bool) -> str:
    """Gerekirse chunk metninin başına madde/başlık bilgisini ekler."""
    body_text = body_text.strip()
    if not prepend_metadata_header:
        return body_text
    header_parts = [article_no.strip()]
    if section_title:
        header_parts.append(section_title.strip())
    header = " | ".join(part for part in header_parts if part)
    if not header:
        return body_text
    if not body_text:
        return header
    return f"{header}\n\n{body_text}"

def _looks_like_section_title(line: str) -> bool:
    """Basit heuristikle bölüm başlığı olup olmadığını kontrol eder."""
    line = line.strip()
    if not line:
        return False
    if len(line) > 60:
        return False
    if any(ch in line for ch in [".", ":", ";"]):
        return False
    if line.startswith("("):
        return False
    return True


def extract_section_title_and_body(article_text: str,
                                   pre_detected: Optional[str] = None) -> (Optional[str], str):
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
    section_title = pre_detected

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i == 0 and _looks_like_section_title(line):
            section_title = section_title or line
            i += 1
            continue

        if i == 0:
            # İlk satırı olduğu gibi ekle (genelde "MADDE X – ...")
            new_lines.append(lines[i])
            i += 1
            continue

        # Eğer henüz section_title bulunmamışsa ve bu satır başlık kriterini sağlıyorsa
        if section_title is None:
            # Çok uzun değil, içinde nokta, iki nokta vb. yok, parantezle başlamıyor
            if _looks_like_section_title(line):
                section_title = line
                # Bu satırı body'ye eklemiyoruz; sadece metadata olarak alıyoruz
                i += 1
                continue

        # Normal satır
        new_lines.append(lines[i])
        i += 1

    cleaned_text = "\n".join(new_lines).strip()
    return section_title, cleaned_text



def _find_heading_start(full_text: str, match_start: int) -> (int, Optional[str]):
    """MADDE satırından hemen önceki olası kısa başlığın başlangıcını döner."""
    idx = match_start
    while idx > 0 and full_text[idx - 1] in " \t\n":
        idx -= 1

    if idx == 0:
        return match_start, None

    line_end = idx
    line_start = full_text.rfind("\n", 0, line_end - 1) + 1
    candidate = full_text[line_start:line_end].strip()

    if _looks_like_section_title(candidate) and not candidate.upper().startswith("MADDE"):
        return line_start, candidate

    return match_start, None


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

    article_starts: List[int] = []
    headings: List[Optional[str]] = []

    for match in matches:
        start_with_heading, heading = _find_heading_start(full_text, match.start())
        article_starts.append(start_with_heading)
        headings.append(heading)

    for i, match in enumerate(matches):
        start = article_starts[i]
        # Son madde ise sonuna kadar; değilse bir sonraki MADDE'nin başına kadar
        end = article_starts[i + 1] if i + 1 < len(article_starts) else len(full_text)
        article_text = full_text[start:end].strip()
        article_no = f"MADDE {match.group(2)}"
        articles.append(ArticleBlock(
            article_no=article_no,
            start_index=start,
            end_index=end,
            text=article_text,
            section_title=headings[i]
        ))

    return articles


def split_article_into_chunks(article: ArticleBlock,
                              doc_id: str,
                              doc_type: str,
                              doc_name: str,
                              max_chars: int = 1500,
                              short_threshold: int = 600,
                              chunk_params: Optional[ChunkingParams] = None) -> List[Chunk]:
    """
    Tek bir MADDE bloğunu 0, 1 veya daha fazla chunk'e böler.

    Strateji:
        - Önce olası section_title'ı ayıkla.
        - Eğer madde metni kısa/orta ise tek chunk yap.
        - Eğer çok uzunsa paragraf/fıkra bazlı böl.
    """
    params = chunk_params or ChunkingParams(max_chars=max_chars)
    max_chars = params.max_chars
    propagate_section_title = params.propagate_section_title
    overlap_chars = max(0, params.chunk_overlap_chars)
    prepend_header = params.prepend_metadata_header
    force_single_chunk = params.force_single_chunk

    # Önce olası bölüm başlığını ayır
    section_title, body_text = extract_section_title_and_body(article.text, article.section_title)

    # Tek madde chunk zorunluysa veya metin kısa/orta ise tek chunk
    if force_single_chunk or len(body_text) <= max_chars:
        chunk_id = f"{doc_id}_{article.article_no.replace(' ', '').lower()}"
        chunk_section_title = _section_title_for_chunk(section_title, propagate_section_title, 0)
        chunk_body = body_text if body_text else article.text
        chunk_text = _build_chunk_text(chunk_body, article.article_no, chunk_section_title, prepend_header)
        return [Chunk(
            id=chunk_id,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            article_no=article.article_no,
            paragraph_no=None,
            section_title=chunk_section_title,
            text=chunk_text
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
            chunk_index = len(chunks)
            chunk_section_title = _section_title_for_chunk(section_title, propagate_section_title, chunk_index)
            chunk_body = buffer.strip()
            chunk_text = _build_chunk_text(chunk_body, article.article_no, chunk_section_title, prepend_header)
            chunks.append(Chunk(
                id=chunk_id,
                doc_id=doc_id,
                doc_type=doc_type,
                doc_name=doc_name,
                article_no=article.article_no,
                paragraph_no=paragraph_no,
                section_title=chunk_section_title,
                text=chunk_text
            ))

            overlap_seed = ""
            if overlap_chars and chunk_body:
                overlap_seed = chunk_body[-overlap_chars:]
                overlap_seed = overlap_seed.strip()

            if overlap_seed:
                buffer = overlap_seed + ("\n" if not overlap_seed.endswith("\n") else "") + candidate
            else:
                buffer = candidate
            current_paragraphs = [marker]

    if buffer.strip():
        paragraph_no = "-".join(current_paragraphs) if current_paragraphs else None
        chunk_id = f"{doc_id}_{article.article_no.replace(' ', '').lower()}_{len(chunks)+1}"
        chunk_index = len(chunks)
        chunk_section_title = _section_title_for_chunk(section_title, propagate_section_title, chunk_index)
        chunk_text = _build_chunk_text(buffer.strip(), article.article_no, chunk_section_title, prepend_header)
        chunks.append(Chunk(
            id=chunk_id,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            article_no=article.article_no,
            paragraph_no=paragraph_no,
            section_title=chunk_section_title,
            text=chunk_text
        ))

    return chunks



def build_chunks_from_pdf_pages(pages: List[PageText],
                                doc_id: str,
                                doc_type: str,
                                doc_name: str,
                                chunk_params: Optional[ChunkingParams] = None) -> List[Chunk]:
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

    effective_params = chunk_params or ChunkingParams.for_doc_type(doc_type)

    all_chunks: List[Chunk] = []
    for article in article_blocks:
        article_chunks = split_article_into_chunks(
            article=article,
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            chunk_params=effective_params
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
