"""PDF to Notion - 우클릭 컨텍스트 메뉴 도구

PDF 파일을 우클릭 -> "PDF to Notion" 클릭 시 실행된다.
PDF의 각 페이지를 PNG 이미지로 변환한 뒤, 파일 탐색기에서 여러 파일을 복사(Ctrl+C)한 것과
동일한 클립보드 포맷(CF_HDROP)으로 담는다. 이후 원하는 Notion 페이지에서 Ctrl+V 하면
페이지 순서대로 이미지 블록이 삽입된다.

요구 패키지: PyMuPDF (fitz), pywin32
설치: pip install PyMuPDF pywin32
"""
import struct
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import win32clipboard
import win32con
from ctypes import windll

DPI = 200  # 150=용량 절약, 200=기본(권장), 300=고화질


def pdf_to_images(pdf_path: Path) -> list[Path]:
    out_dir = Path(tempfile.gettempdir()) / "pdf_to_notion" / pdf_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    zoom = DPI / 72
    matrix = fitz.Matrix(zoom, zoom)

    image_paths = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix)
            img_path = out_dir / f"{pdf_path.stem}_{i:03d}.png"
            pix.save(img_path)
            image_paths.append(img_path)
    return image_paths


def copy_files_to_clipboard(paths: list[Path]) -> None:
    # DROPFILES 구조체(20바이트 헤더) + UTF-16 이중 널 종료 파일 경로 목록.
    # 파일 탐색기에서 파일을 Ctrl+C 했을 때와 동일한 CF_HDROP 포맷이라
    # Notion 등 대부분의 앱이 "파일 붙여넣기"로 인식해 순서대로 삽입한다.
    file_list = "\0".join(str(p) for p in paths) + "\0\0"
    data = file_list.encode("utf-16-le")
    header = struct.pack("<5l", 20, 0, 0, 0, 1)
    dropfiles = header + data

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, dropfiles)
    finally:
        win32clipboard.CloseClipboard()


def notify(message: str) -> None:
    windll.user32.MessageBoxW(0, message, "PDF to Notion", 0)


def main() -> None:
    if len(sys.argv) < 2:
        notify("PDF 파일 경로가 전달되지 않았습니다.")
        return

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        notify(f"PDF 파일이 아닙니다:\n{pdf_path}")
        return

    try:
        images = pdf_to_images(pdf_path)
        copy_files_to_clipboard(images)
    except Exception as exc:
        notify(f"변환 실패:\n{exc}")
        return

    notify(f"{pdf_path.name}\n{len(images)}페이지 이미지 복사 완료.\nNotion 페이지에서 Ctrl+V 하세요.")


if __name__ == "__main__":
    main()
