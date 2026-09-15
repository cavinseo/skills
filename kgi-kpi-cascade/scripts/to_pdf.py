#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML -> A4 PDF. 흑백 인쇄용 HTML에 쓴다.

    python3 scripts/to_pdf.py report_bw.html report.pdf

Playwright가 있으면 그것을 쓰고, 없으면 wkhtmltopdf를 찾는다.
둘 다 없으면 브라우저에서 직접 인쇄(Ctrl+P → PDF로 저장)해도 결과는 같다.
스타일시트에 @page/@media print 규칙이 들어 있기 때문이다.
"""
import os, shutil, subprocess, sys


def with_playwright(src, dst):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + os.path.abspath(src))
        pg.wait_for_timeout(1500)          # 웹폰트 로딩 대기
        pg.pdf(path=dst, format="A4", print_background=True)
        b.close()
    return True


def with_wkhtmltopdf(src, dst):
    exe = shutil.which("wkhtmltopdf")
    if not exe:
        return False
    subprocess.run([exe, "--page-size", "A4", "--print-media-type", src, dst], check=True)
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    try:
        with_playwright(src, dst)
    except ImportError:
        if not with_wkhtmltopdf(src, dst):
            print("Playwright도 wkhtmltopdf도 없다.\n"
                  "  pip install playwright && playwright install chromium\n"
                  "또는 브라우저에서 Ctrl+P → PDF로 저장.", file=sys.stderr)
            return 1
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
