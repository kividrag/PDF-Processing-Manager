import pdfplumber

def extract_text_with_precision(pdf_path):
    """
    Extracts text from a PDF preserving layout and physical spacing.
    """
    full_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # extract_text(layout=True) attempts to replicate the physical layout
                # This is slower but much more precise for columns/tables.
                text = page.extract_text(layout=True)

                if text:
                    full_text += text + "\n"

        return full_text

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Usage
    pdf_file = r"D:\1_Work\1_'Projects'\AI\2025\MediaEval 2025\MediaEval2025_UsageAgreement.pdf"
    extracted_content = extract_text_with_precision(pdf_file)
    print(extracted_content)