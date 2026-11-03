
from pathlib import Path
import pymupdf

DATA_DIR = Path(__file__).parent / "data"
YEARS = ["2016", "2017", "2021", "2025"]

for year in YEARS:
    folder = DATA_DIR / year

    print("\n" + "=" * 65)
    print(f"YEAR: {year}")
    print("=" * 65)

    for pdf_path in sorted(folder.rglob("*.pdf")):
        print(f"\nPDF: {pdf_path.name}")

        with pymupdf.open(pdf_path) as doc:
            no_text_pages = []

            for page_number, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()

                if not text:
                    images = page.get_images(full=True)

                    no_text_pages.append({
                        "page": page_number,
                        "images": len(images)
                    })

            print(f"Pages needing inspection: {len(no_text_pages)}")

            for item in no_text_pages[:15]:
                print(
                    f"Page {item['page']}: "
                    f"{item['images']} embedded image(s)"
                )

            if len(no_text_pages) > 15:
                print("Only first 15 pages displayed.")
