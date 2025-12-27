import os
import re
import pymupdf.layout
import pymupdf4llm


def extract_text_with_precision(pdf_path):
    """
    Extracts text from a PDF using pymupdf4llm for fast Markdown conversion.
    """
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            print(f"Error: File not found at {pdf_path}")
            return None

        print(f"Converting {pdf_path} using pymupdf4llm...")

        # specific_pages parameter can be used if you only want certain pages
        # e.g., to_markdown(pdf_path, pages=[0, 1, 2])
        full_text = pymupdf4llm.to_markdown(pdf_path)

        # --- Post-Processing to remove References ---
        # pymupdf4llm generates clean Markdown headers, making regex matching reliable.

        lower_text = full_text.lower()
        split_index = -1

        pattern = re.compile(r'(?im)^#{2,}.*?references\b')  # case-insensitive, multiline
        m = pattern.search(lower_text)
        if m:
            split_index = m.start()
            print("match found at index:", m.start())  # index of match in the full string
            print("matched text:", repr(m.group()))
        else:
            print("no match")

        if split_index != -1:
            print("References section detected and removed.")
            res = full_text[:split_index].strip()
        else:
            res = full_text.strip()

        return res

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    # Note: Ensure you have installed the library:
    # pip install pymupdf4llm

    pdf_file = r"D:\3_PC\temp\Repo_Draft\papers-2025-W05\2501.13925.pdf"

    extracted_content = extract_text_with_precision(pdf_file)

    if extracted_content:
        # Saving to file
        output_file = pdf_file.replace(".pdf", ".md")

        # Ensure we don't accidentally overwrite the source if extensions match (unlikely here)
        if output_file == pdf_file:
            output_file += ".md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_content)

        print(f"\n--- Extraction Complete ---\nSaved to: {output_file}")

        # Print preview
        print("\nPreview (first 500 chars):")
        print(extracted_content[:500])
