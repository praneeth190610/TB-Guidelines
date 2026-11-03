
from pathlib import Path
import pymupdf

# Main folder containing the four guideline-year folders
DATA_DIR = Path(__file__).parent / "data"

YEARS = ["2016", "2017", "2021", "2025"]


def inspect_pdf(pdf_path):
    print("\n" + "=" * 70)
    print(f"FILE: {pdf_path.name}")
    print("=" * 70)

    try:
        with pymupdf.open(pdf_path) as document:
            total_pages = len(document)
            pages_with_text = 0
            total_characters = 0

            print(f"Total pages: {total_pages}")

            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text("text")
                character_count = len(page_text.strip())

                if character_count > 0:
                    pages_with_text += 1
                    total_characters += character_count

            print(f"Pages containing text: {pages_with_text}")
            print(f"Pages without text: {total_pages - pages_with_text}")
            print(f"Total extracted characters: {total_characters}")

            if total_characters > 0:
                print("Status: Text extraction successful")
            else:
                print("Status: No selectable text found; OCR may be needed")

    except Exception as error:
        print(f"ERROR: Could not read PDF: {error}")


def main():
    print("\nTB GUIDELINE PDF INSPECTION")
    print("=" * 70)

    for year in YEARS:
        year_folder = DATA_DIR / year

        print(f"\n\nYEAR: {year}")
        print("-" * 70)

        if not year_folder.exists():
            print(f"ERROR: Folder not found: {year_folder}")
            continue

        pdf_files = list(year_folder.rglob("*.pdf"))

        if not pdf_files:
            print("No PDF files found in this folder.")
            continue

        for pdf_path in pdf_files:
            inspect_pdf(pdf_path)

    print("\n\nINSPECTION COMPLETED")


if __name__ == "__main__":
    main()
