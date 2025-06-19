import fitz
import json

def test_pdf_highlights(pdf_path):
    """Test highlight extraction from a PDF file."""
    print(f"\nTesting PDF: {pdf_path}")
    print("-" * 50)
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    print(f"Number of pages: {len(doc)}")
    
    # Process each page
    all_highlights = []
    
    for page_num, page in enumerate(doc, 1):
        print(f"\nProcessing page {page_num}")
        
        # Get all annotations
        annots = list(page.annots())
        if not annots:
            print("No annotations found on this page")
            continue
            
        print(f"Found {len(annots)} annotations")
        
        # Process each annotation
        for i, annot in enumerate(annots, 1):
            print(f"\nAnnotation {i}:")
            print(f"Type: {annot.type}")  # Get annotation type
            
            # Try to get colors if available
            try:
                colors = annot.colors
                print(f"Colors: {colors}")
            except AttributeError:
                colors = None
                print("No color information available")
            
            # Check if it's a highlight (type 8)
            if annot.type[0] == 8:
                rect = annot.rect
                highlighted_text = page.get_text("text", clip=rect).strip()
                print(f"Highlighted text: {highlighted_text}")
                
                all_highlights.append({
                    'page': page_num,
                    'text': highlighted_text,
                    'type': 'highlight',
                    'color': colors.get('stroke') if colors else None
                })
            else:
                print(f"Not a highlight annotation (type {annot.type})")
    
    # Print summary
    print("\nSummary:")
    print("-" * 50)
    print(f"Total highlights found: {len(all_highlights)}")
    if all_highlights:
        print("\nExtracted highlights:")
        print(json.dumps(all_highlights, indent=2))
    
    doc.close()
    return all_highlights

if __name__ == "__main__":
    test_pdf_highlights("Project PDF.pdf") 