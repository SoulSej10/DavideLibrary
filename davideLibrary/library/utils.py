import io
from PIL import Image
import qrcode
from django.core.files.base import ContentFile
from django.conf import settings

def generate_qr_code(book_number):
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(book_number)
    qr.make(fit=True)

    # Create an image
    img = qr.make_image(fill='black', back_color='white')
    
    # Save to BytesIO
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    image_file = ContentFile(buffered.getvalue(), f"{book_number}.png")
    
    return image_file
