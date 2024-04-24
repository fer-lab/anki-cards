import os
import re
import json
from unidecode import unidecode
from PIL import Image, ImageDraw, ImageFont, ImageOps

current_directory = os.path.dirname(__file__)

def create_image_with_text_webp(name=None, color = None, alias = None, create_question = True):

    if name is None:
        raise ValueError("name must be specified")

    name = name.title()

    if color is None:
        raise ValueError("color_hex and must be specified")

    if alias is None:
        alias = name

    # create from name. no spaces, lowercase, no accents
    alias = alias.replace(" ", "_").lower()
    # remove accents. á -> a. é -> e. etc all special characters..
    alias = unidecode(alias)
    # remove special characters. avoid double __
    alias = re.sub(r'\W+', '', alias)

    # Convert the color from hex to RGB
    color_rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))

    # Calculate the luminance
    luminance = (0.299 * color_rgb[0] + 0.587 * color_rgb[1] + 0.114 * color_rgb[2]) / 255

    # Choose the text color based on the luminance
    text_color = "black" if luminance > 0.5 else "white"


    # Size of the image from the original example
    image_size = (400, 100)
    # Create a new image with the specified color
    image = Image.new('RGB', image_size, color)
    # Get a font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    # Draw the text in the middle of the rectangle, in black
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_x = (image_size[0] - (text_bbox[2] - text_bbox[0])) / 2
    text_y = (image_size[1] - (text_bbox[3] - text_bbox[1])) / 2
    draw.text((text_x, text_y), name, font=font, fill=text_color)

    border_size = 10  # Change this to adjust the size of the border
    image = ImageOps.expand(image, border=border_size, fill='white')

    # Save the image to a file with .webp extension
    image_tmp_path = os.path.dirname(os.path.dirname(current_directory))
    filepath = os.path.join(image_tmp_path, "temp", f'{alias}.webp')
    print("Saving image to ", filepath)
    image.save(filepath, 'WEBP')

    if create_question:
        create_image_with_text_webp(name="Quelle Couleur ?", color=color, alias=f"{alias}.q", create_question=False)

    return filepath


# Call the updated function

with open(os.path.join(current_directory, 'colors.json'), 'r') as f:
    colors = json.load(f)

# Now you can use the colors list as before
for color_dict in colors:

    create_image_with_text_webp(name="Quelle Couleur ?", alias=color_dict["name"], color=color_dict["code"], create_question=False)
