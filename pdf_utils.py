import PyPDF2
import os
import pdfplumber
import pytesseract

def split_pdf(input_pdf_path, output_pdf_paths, page_groups):
    # Open the input PDF file
    with open(input_pdf_path, 'rb') as input_pdf_file:
        reader = PyPDF2.PdfReader(input_pdf_file)
        
        # Ensure the output directory exists
        for output_pdf_path in output_pdf_paths:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        
        # Iterate over each group of pages
        for output_pdf_path, pages in zip(output_pdf_paths, page_groups):
            writer = PyPDF2.PdfWriter()
            
            # Add specified pages to the writer
            for page_num in pages:
                try:
                    # Subtract 1 because PyPDF2 uses zero-based indexing
                    writer.add_page(reader.pages[page_num - 1])
                except IndexError:
                    print(f"Page number {page_num} is out of range for {input_pdf_path}")
                    continue
            
            # Write the new PDF to a file
            try:
                with open(output_pdf_path, 'wb') as output_pdf_file:
                    writer.write(output_pdf_file)
            except Exception as e:
                print(f"Failed to write {output_pdf_path}: {e}")

def process_pdf_files(pdf_dir, txt_dir):
    os.makedirs(txt_dir, exist_ok=True)  # Create the directory if it doesn't exist

    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

    for pdf_file in pdf_files:
        with pdfplumber.open(pdf_file) as pdf:
            all_text = []
            # Loop through all the pages
            for page_num, page in enumerate(pdf.pages):
                # Extract text from the current page
                text = page.extract_text()
                
                if text:
                    all_text.append(text)
                else:
                    # Attempt OCR on the page
                    image = page.to_image()
                    ocr_text = pytesseract.image_to_string(image.original)
                    if ocr_text.strip():
                        all_text.append(ocr_text)
                    else:
                        all_text.append("This page may contain images or non-standard text encoding.")

            # Save the extracted text to a .txt file
            txt_file_path = os.path.join(txt_dir, f"{os.path.splitext(os.path.basename(pdf_file))[0]}.txt")
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write("\n\n".join(all_text))
# Define the input PDF path
input_pdf_path = 'resumes/resume.pdf'

# Define the output PDF paths and corresponding page groups
output_pdf_paths = [
    'resumes/resume_extracted/resume_1_4_5.pdf',
    'resumes/resume_extracted/resume_6_9_10.pdf',
    'resumes/resume_extracted/resume_1_3_4.pdf',
    'resumes/resume_extracted/resume_6_9_8.pdf',
    'resumes/resume_extracted/resume_1_2_5.pdf',
    'resumes/resume_extracted/resume_6_7_10.pdf',
    'resumes/resume_extracted/resume_1_2_3.pdf',
    'resumes/resume_extracted/resume_6_7_8.pdf',
    'resumes/resume_extracted/resume_1_2.pdf',
    'resumes/resume_extracted/resume_6_7.pdf',
    'resumes/resume_extracted/resume_1_3.pdf',
    'resumes/resume_extracted/resume_6_8.pdf'
]

page_groups = [
    [1, 4, 5],
    [6, 9, 10],
    [1, 3, 4],
    [6, 9, 8],
    [1, 2, 5],
    [6, 7, 10],
    [1, 2, 3],
    [6, 7, 8],
    [1, 2],
    [6, 7],
    [1, 3],
    [6, 8]
] 
def main():
    split_pdf(input_pdf_path, output_pdf_paths, page_groups)
    pdf_dir = "resumes/resume_extracted"
    txt_dir = "resumes/txt_extracted"
    process_pdf_files(pdf_dir, txt_dir)

if __name__ == "__main__":
    main()
