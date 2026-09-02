import os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

FONT_PATH = "assets/fonts/Vazirmatn-Regular.ttf"

def generate_message_image(text: str, width: int = 800, height: int = 800) -> str:
    """Generates an image from a message with RTL support."""
    # Create a solid color background image
    img = Image.new('RGB', (width, height), color=(250, 245, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONT_PATH, size=40)
    except IOError:
        font = ImageFont.load_default()

    # Reshape and handle bidi
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)

    # Calculate text bounding box
    bbox = draw.multiline_textbbox((0, 0), bidi_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position text in center
    x = (width - text_width) / 2
    y = (height - text_height) / 2

    # Draw text
    draw.multiline_text((x, y), bidi_text, font=font, fill=(50, 50, 50), align='center')

    output_path = f"assets/temp_image_{hash(text)}.png"
    img.save(output_path)
    return output_path
