import pypdf
import re
from typing import Dict, Any, List
import fitz  # PyMuPDF
import pandas as pd
import os

def extract_variables_from_pdf(pdf_path: str, variable_patterns: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract specific variables from a PDF file using regex patterns.
    
    Args:
        pdf_path (str): Path to the PDF file
        variable_patterns (dict): Dictionary of variable names and their regex patterns
        
    Returns:
        dict: Dictionary containing the extracted variables and their values
    """
    # Initialize the results dictionary
    results = {var_name: None for var_name in variable_patterns}
    
    try:
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = pypdf.PdfReader(file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Search for each variable using the provided patterns
            for var_name, pattern in variable_patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    results[var_name] = matches[0]  # Get the first match
                    
        return results
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return results

def main():
    # Example usage
    pdf_path = "Project PDF.pdf"
    output_dir = "."
    
    try:
        with PDFFieldExtractor(pdf_path) as extractor:
            fields = extractor.extract_fields()
            print("\nExtracted Fields:")
            print("-" * 50)
            for field, value in fields.items():
                print(f"{field}: {value}")
            
            csv_path = extractor.to_csv(output_dir)
            print(f"\nExtracted data saved to: {csv_path}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

class PDFFieldExtractor:
    # Field definitions with their possible labels and patterns
    FIELD_PATTERNS = {
        'company_name': {
            'labels': ['company name', 'business name', 'supplier', 'vendor'],
            'pattern': r'([A-Z][A-Za-z0-9\s\.,&]+(Ltd|Limited|Inc|LLC|LLP|Corporation|Corp|Company|Co)\b)',
            'type': 'text'
        },
        'document_number': {
            'labels': ['document no', 'invoice no', 'reference no', 'order no'],
            'pattern': r'\b\d{6,12}\b',
            'type': 'number'
        },
        'sold_to_party': {
            'labels': ['sold to party', 'customer', 'bill to', 'sold to'],
            'pattern': r'(?:sold to party|customer|bill to|sold to)[:.]?\s*(\d+|\w+)',
            'type': 'text'
        },
        'reference': {
            'labels': ['your reference', 'customer reference', 'ref'],
            'pattern': r'(?:your reference|ref)[:.]?\s*([A-Za-z0-9-_/]+)',
            'type': 'text'
        },
        'total_net': {
            'labels': ['total net', 'net amount', 'subtotal', 'net value'],
            'pattern': r'(?:£|EUR|USD)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'type': 'amount'
        },
        'vat': {
            'labels': ['vat', 'tax', 'gst', 'sales tax'],
            'pattern': r'(?:£|EUR|USD)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'type': 'amount'
        },
        'total_due': {
            'labels': ['total due', 'total amount', 'total payable', 'total inc vat', 'total including vat'],
            'pattern': r'(?:£|EUR|USD)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'type': 'amount'
        }
    }

    def __init__(self, pdf_path: str):
        """Initialize the PDF field extractor.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.extracted_fields = {}

    def extract_fields(self) -> Dict[str, Any]:
        """Extract all defined fields from the PDF.
        
        Returns:
            Dict[str, Any]: Dictionary containing the extracted fields and their values
        """
        # Extract text from all pages
        full_text = ""
        for page in self.doc:
            full_text += page.get_text()

        # Process each field
        for field_name, field_info in self.FIELD_PATTERNS.items():
            value = self._extract_field(full_text, field_info)
            if value:
                self.extracted_fields[field_name] = value

        return self.extracted_fields

    def _extract_field(self, text: str, field_info: Dict) -> str:
        """Extract a specific field from the text using its patterns and labels.
        
        Args:
            text (str): Text to search in
            field_info (Dict): Field definition including labels and pattern
            
        Returns:
            str: Extracted value or None if not found
        """
        # First try to find the field using labels
        for label in field_info['labels']:
            # Create a pattern that looks for the label followed by a value
            label_pattern = rf'{label}[:\s]+(.*?)(?:\n|$)'
            matches = re.finditer(label_pattern, text.lower())
            
            for match in matches:
                # Get the text after the label
                value_text = match.group(1).strip()
                # Try to extract the value using the field's pattern
                value_match = re.search(field_info['pattern'], value_text, re.IGNORECASE)
                if value_match:
                    return self._clean_value(value_match.group(0), field_info['type'])

        # If no value found using labels, try the pattern directly
        matches = re.finditer(field_info['pattern'], text, re.IGNORECASE)
        for match in matches:
            return self._clean_value(match.group(0), field_info['type'])

        return None

    def _clean_value(self, value: str, value_type: str) -> str:
        """Clean the extracted value based on its type.
        
        Args:
            value (str): Value to clean
            value_type (str): Type of the value ('text', 'number', 'amount')
            
        Returns:
            str: Cleaned value
        """
        if not value:
            return None

        value = value.strip()

        if value_type == 'amount':
            # Remove currency symbols and spaces
            value = re.sub(r'[£$€\s]', '', value)
            # Ensure proper decimal format
            if ',' in value and '.' not in value:
                value = value.replace(',', '.')
            elif ',' in value and '.' in value:
                value = value.replace(',', '')
            return value

        elif value_type == 'number':
            # Remove any non-digit characters
            return re.sub(r'\D', '', value)

        else:  # text
            # Remove extra whitespace
            return ' '.join(value.split())

    def to_csv(self, output_path: str) -> str:
        """Save extracted fields to CSV file.
        
        Args:
            output_path (str): Path where to save the CSV file
            
        Returns:
            str: Path to the created CSV file
        """
        if not self.extracted_fields:
            self.extract_fields()

        # Convert to DataFrame
        df = pd.DataFrame([self.extracted_fields])
        
        # Save to CSV
        csv_path = os.path.join(output_path, 
                              f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_extracted.csv")
        df.to_csv(csv_path, index=False)
        return csv_path

    def close(self):
        """Close the PDF document."""
        self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == "__main__":
    main() 