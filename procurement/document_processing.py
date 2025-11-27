"""
Document Processing Service
Handles extraction of data from proforma invoices and receipts using OCR and PDF parsing
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    PROCESSING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Document processing libraries not available: {e}")
    PROCESSING_AVAILABLE = False

try:
    from groq import Groq
    from django.conf import settings
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("Groq library not available. Install with: pip install groq")
    GROQ_AVAILABLE = False


class DocumentProcessor:
    """Base class for document processing"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        if not PROCESSING_AVAILABLE:
            return ""
        
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_image(file_path: str) -> str:
        """Extract text from image using OCR"""
        if not PROCESSING_AVAILABLE:
            return ""
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    @staticmethod
    def pdf_to_ocr(file_path: str) -> str:
        """Convert PDF to images and perform OCR (for scanned PDFs)"""
        if not PROCESSING_AVAILABLE:
            return ""
        
        try:
            images = convert_from_path(file_path, dpi=300)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            return text
        except Exception as e:
            logger.error(f"Error performing OCR on PDF: {e}")
            return ""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from document (PDF or image)
        Tries PDF extraction first, falls back to OCR if needed
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        
        if extension == '.pdf':
            # Try PDF text extraction first
            text = DocumentProcessor.extract_text_from_pdf(file_path)
            
            # If text is sparse, try OCR
            if len(text.strip()) < 100:
                logger.info("PDF text sparse, trying OCR")
                text = DocumentProcessor.pdf_to_ocr(file_path)
            
            return text
        
        elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return DocumentProcessor.extract_text_from_image(file_path)
        
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return ""
    @staticmethod
    def extract_with_groq(text: str, doc_type: str) -> Dict:
        """
        Extract structured data using Groq API
        doc_type: 'proforma' or 'receipt'
        """
        if not GROQ_AVAILABLE or not getattr(settings, 'GROQ_API_KEY', None):
            logger.warning("Groq not available or API key missing")
            return {}

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            system_prompt = """
            You are a precise document extraction AI. Extract data from the provided text and return ONLY a valid JSON object.
            Do not include any markdown formatting like ```json ... ```. Just the raw JSON string.
            
            For 'proforma' or 'invoice':
            {
                "vendor": "Vendor Name",
                "vendor_address": "Vendor Address",
                "items": [
                    {"name": "Item Description", "quantity": 1, "unit_price": 100.0, "total": 100.0}
                ],
                "subtotal": 100.0,
                "tax": 10.0,
                "total": 110.0,
                "payment_terms": "Net 30"
            }
            
            For 'receipt':
            {
                "vendor": "Vendor Name",
                "items": [
                    {"name": "Item Description", "quantity": 1, "unit_price": 10.0, "total": 10.0}
                ],
                "total": 10.0
            }
            
            Ensure all numbers are floats or integers. If a field is not found, use null or empty string/list.
            """
            
            user_prompt = f"Document Type: {doc_type}\n\nText Content:\n{text[:8000]}"
            
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            import json
            data = json.loads(response_content)
            return data
            
        except Exception as e:
            logger.error(f"Groq extraction failed: {e}")
            return {}


class ProformaExtractor(DocumentProcessor):
    """Extract structured data from proforma invoices"""
    
    @staticmethod
    def extract_vendor(text: str) -> Dict[str, str]:
        """Extract vendor information from document text"""
        lines = text.split('\n')
        vendor_data = {
            'vendor': '',
            'vendor_address': ''
        }
        
        # Try to find vendor name in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and len(line) > 3:
                # Skip common headers
                if any(header in line.lower() for header in ['invoice', 'proforma', 'quotation', 'date']):
                    continue
                if not vendor_data['vendor']:
                    vendor_data['vendor'] = line
                elif not vendor_data['vendor_address'] and i < 5:
                    vendor_data['vendor_address'] += line + " "
        
        vendor_data['vendor_address'] = vendor_data['vendor_address'].strip()
        return vendor_data
    
    @staticmethod
    def extract_items(text: str) -> List[Dict]:
        """Extract line items from document"""
        items = []
        lines = text.split('\n')
        
        # Patterns for detecting item lines
        # Looking for: quantity, description, unit price, total
        price_pattern = r'[\$€£]?\s*(\d+[,.]?\d*\.?\d+)'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for lines with prices
            prices = re.findall(price_pattern, line)
            if len(prices) >= 2:  # At least unit price and total
                # Extract quantities (numbers at start of line)
                qty_match = re.match(r'^(\d+)', line)
                quantity = int(qty_match.group(1)) if qty_match else 1
                
                # Extract description (text between quantity and first price)
                desc_match = re.search(r'^\d*\s*([A-Za-z].*?)\s*[\$€£]?\s*\d', line)
                description = desc_match.group(1).strip() if desc_match else line
                
                # Clean prices
                unit_price = float(prices[-2].replace(',', ''))
                total = float(prices[-1].replace(',', ''))
                
                items.append({
                    'name': description[:100],  # Limit length
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })
        
        return items
    
    @staticmethod
    def extract_totals(text: str) -> Dict[str, float]:
        """Extract subtotal, tax, and total amounts"""
        totals = {
            'subtotal': 0.0,
            'tax': 0.0,
            'total': 0.0
        }
        
        lines = text.split('\n')
        price_pattern = r'[\$€£]?\s*(\d+[,.]?\d*\.?\d+)'
        
        for line in lines:
            line_lower = line.lower()
            
            if 'subtotal' in line_lower:
                match = re.search(price_pattern, line)
                if match:
                    totals['subtotal'] = float(match.group(1).replace(',', ''))
            
            elif 'tax' in line_lower or 'vat' in line_lower:
                match = re.search(price_pattern, line)
                if match:
                    totals['tax'] = float(match.group(1).replace(',', ''))
            
            elif 'total' in line_lower and 'subtotal' not in line_lower:
                match = re.search(price_pattern, line)
                if match:
                    totals['total'] = float(match.group(1).replace(',', ''))
        
        return totals
    
    @staticmethod
    def extract_payment_terms(text: str) -> str:
        """Extract payment terms from document"""
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if 'payment' in line_lower or 'terms' in line_lower:
                # Look for common patterns like "Net 30", "Due on receipt", etc.
                if 'net' in line_lower or 'due' in line_lower or 'days' in line_lower:
                    return line.strip()
        
        return ""
    
    @classmethod
    def extract_data(cls, file_path: str) -> Dict:
        """
        Extract all data from proforma invoice
        Returns structured dictionary with vendor, items, totals, etc.
        """
        if not PROCESSING_AVAILABLE:
            return {
                'error': 'Document processing libraries not available',
                'vendor': '',
                'items': [],
                'total': 0.0
            }
        
        try:
            # Extract text
            text = cls.extract_text(file_path)
            
            if not text:
                return {
                    'error': 'Could not extract text from document',
                    'vendor': '',
                    'items': [],
                    'total': 0.0
                }
            
            # Try AI extraction first if enabled
            if getattr(settings, 'USE_AI_EXTRACTION', True) and GROQ_AVAILABLE:
                try:
                    logger.info("Attempting AI extraction for proforma...")
                    ai_data = cls.extract_with_groq(text, 'proforma')
                    if ai_data and ai_data.get('vendor') and ai_data.get('total'):
                        logger.info("AI extraction successful")
                        ai_data['extraction_method'] = 'ai_groq'
                        return ai_data
                except Exception as e:
                    logger.warning(f"AI extraction failed, falling back to regex: {e}")

            # Fallback to regex extraction
            vendor_data = cls.extract_vendor(text)
            items = cls.extract_items(text)
            totals = cls.extract_totals(text)
            payment_terms = cls.extract_payment_terms(text)
            
            return {
                'vendor': vendor_data['vendor'],
                'vendor_address': vendor_data['vendor_address'],
                'items': items,
                'subtotal': totals['subtotal'],
                'tax': totals['tax'],
                'total': totals['total'],
                'payment_terms': payment_terms,
                'extraction_method': 'regex_fallback'
            }
        
        except Exception as e:
            logger.error(f"Error extracting proforma data: {e}")
            return {
                'error': str(e),
                'vendor': '',
                'items': [],
                'total': 0.0
            }


class ReceiptValidator(DocumentProcessor):
    """Validate receipts against purchase orders"""
    
    @classmethod
    def extract_receipt_data(cls, file_path: str) -> Dict:
        """Extract data from receipt"""
        try:
            text = cls.extract_text(file_path)
            
            if not text:
                return {'error': 'Could not extract text from receipt'}
            
            # Try AI extraction first if enabled
            if getattr(settings, 'USE_AI_EXTRACTION', True) and GROQ_AVAILABLE:
                try:
                    logger.info("Attempting AI extraction for receipt...")
                    ai_data = cls.extract_with_groq(text, 'receipt')
                    if ai_data and ai_data.get('total'):
                        logger.info("AI extraction successful")
                        ai_data['extraction_method'] = 'ai_groq'
                        return ai_data
                except Exception as e:
                    logger.warning(f"AI extraction failed, falling back to regex: {e}")

            # Use similar extraction methods as proforma
            vendor_data = ProformaExtractor.extract_vendor(text)
            items = ProformaExtractor.extract_items(text)
            totals = ProformaExtractor.extract_totals(text)
            
            return {
                'vendor': vendor_data['vendor'],
                'items': items,
                'total': totals['total'],
                'extraction_method': 'regex_fallback'
            }
        
        except Exception as e:
            logger.error(f"Error extracting receipt data: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def fuzzy_match(str1: str, str2: str, threshold: float = 0.7) -> bool:
        """Simple fuzzy string matching"""
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return True
        
        # Check if one contains the other
        if str1 in str2 or str2 in str1:
            return True
        
        # Simple similarity check
        common_chars = sum(1 for c in str1 if c in str2)
        similarity = common_chars / max(len(str1), len(str2))
        
        return similarity >= threshold
    
    @classmethod
    def validate_against_po(cls, receipt_data: Dict, po_data: Dict) -> Dict:
        """
        Validate receipt against purchase order
        Returns validation results with discrepancies
        """
        discrepancies = []
        
        # Validate vendor
        receipt_vendor = receipt_data.get('vendor', '')
        po_vendor = po_data.get('vendor_name', '') or po_data.get('vendor', '')
        
        if receipt_vendor and po_vendor:
            if not cls.fuzzy_match(receipt_vendor, po_vendor, threshold=0.6):
                discrepancies.append({
                    'field': 'vendor',
                    'expected': po_vendor,
                    'actual': receipt_vendor,
                    'severity': 'high'
                })
        
        # Validate items
        receipt_items = receipt_data.get('items', [])
        po_items = po_data.get('extracted_items', []) or po_data.get('items', [])
        
        if isinstance(po_items, list):
            for po_item in po_items:
                po_name = po_item.get('name', '')
                po_price = float(po_item.get('unit_price', 0))
                
                # Find matching item in receipt
                matched = False
                for receipt_item in receipt_items:
                    receipt_name = receipt_item.get('name', '')
                    receipt_price = float(receipt_item.get('unit_price', 0))
                    
                    if cls.fuzzy_match(po_name, receipt_name, threshold=0.6):
                        matched = True
                        
                        # Check price difference (allow 5% tolerance)
                        price_diff = abs(receipt_price - po_price)
                        tolerance = po_price * 0.05
                        
                        if price_diff > tolerance:
                            discrepancies.append({
                                'field': 'item_price',
                                'item': po_name,
                                'expected': po_price,
                                'actual': receipt_price,
                                'difference': price_diff,
                                'severity': 'high' if price_diff > po_price * 0.1 else 'medium'
                            })
                        break
                
                if not matched:
                    discrepancies.append({
                        'field': 'item_missing',
                        'item': po_name,
                        'severity': 'high'
                    })
        
        # Validate total
        receipt_total = receipt_data.get('total', 0)
        po_total = float(po_data.get('total_amount', 0))
        
        if receipt_total and po_total:
            total_diff = abs(receipt_total - po_total)
            tolerance = po_total * 0.05
            
            if total_diff > tolerance:
                discrepancies.append({
                    'field': 'total',
                    'expected': po_total,
                    'actual': receipt_total,
                    'difference': total_diff,
                    'severity': 'high'
                })
        
        # Calculate match score
        total_checks = 3 + len(po_items) if isinstance(po_items, list) else 3
        failed_checks = len(discrepancies)
        match_score = max(0, (total_checks - failed_checks) / total_checks)
        
        return {
            'valid': len(discrepancies) == 0,
            'discrepancies': discrepancies,
            'match_score': round(match_score, 2),
            'total_checks': total_checks,
            'failed_checks': failed_checks
        }


# Convenience functions
def extract_proforma_data(file_path: str) -> Dict:
    """Extract data from proforma invoice"""
    return ProformaExtractor.extract_data(file_path)


def validate_receipt(receipt_path: str, purchase_order) -> Dict:
    """Validate receipt against purchase order"""
    receipt_data = ReceiptValidator.extract_receipt_data(receipt_path)
    
    if 'error' in receipt_data:
        return receipt_data
    
    po_data = {
        'vendor_name': purchase_order.vendor_name,
        'vendor': purchase_order.vendor,
        'extracted_items': purchase_order.extracted_items,
        'items': purchase_order.items,
        'total_amount': purchase_order.total_amount
    }
    
    validation_result = ReceiptValidator.validate_against_po(receipt_data, po_data)
    validation_result['receipt_data'] = receipt_data
    
    return validation_result
