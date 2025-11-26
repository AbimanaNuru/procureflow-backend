from PIL import Image, ImageDraw, ImageFont
import os

def create_image_with_text(filename, text):
    # Create a white image
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)
    
    # Use default font
    # In a real environment we might want to load a ttf, but default is safer for portability
    # Default font is very small, so we'll just write line by line with spacing
    
    y_position = 20
    for line in text.split('\n'):
        d.text((20, y_position), line, fill='black')
        y_position += 15  # Adjust line height
        
    img.save(filename)
    print(f"Created {filename}")

def generate_proforma():
    text = """
    PROFORMA INVOICE
    Date: 2023-10-27
    
    Vendor Details:
    Tech Solutions Inc.
    123 Tech Park, Silicon Valley, CA
    
    Bill To:
    ProcureFlow Corp
    
    Items:
    1 MacBook Pro 16-inch    $2500.00    $2500.00
    2 Monitor 4K             $500.00     $1000.00
    
    Subtotal: $3500.00
    Tax: $350.00
    Total: $3850.00
    
    Payment Terms: Net 30 Days
    """
    create_image_with_text("proforma_test.png", text)

def generate_receipt():
    text = """
    RECEIPT
    Date: 2023-11-01
    
    Vendor:
    Tech Solutions Inc.
    
    Items:
    1 MacBook Pro 16-inch    $2500.00    $2500.00
    2 Monitor 4K             $500.00     $1000.00
    
    Total: $3850.00
    
    Paid in Full
    """
    create_image_with_text("receipt_test.png", text)

def generate_mismatched_receipt():
    text = """
    RECEIPT
    Date: 2023-11-01
    
    Vendor:
    Wrong Vendor LLC
    
    Items:
    1 Gaming Laptop          $2000.00    $2000.00
    
    Total: $2000.00
    """
    create_image_with_text("receipt_mismatch_test.png", text)

if __name__ == "__main__":
    generate_proforma()
    generate_receipt()
    generate_mismatched_receipt()
