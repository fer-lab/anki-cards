import re
import os

import genanki
from PIL import Image

def convert_to_webp(input_image_path, output_image_path):
    image = Image.open(input_image_path)
    image.save(output_image_path, 'webp')

def text_to_strings(source_file):


    basename = os.path.basename(source_file)
    script_name, _ = os.path.splitext(basename)
    namespace = os.path.basename(os.path.dirname(source_file))
    base_path = package_location()

    return f"{base_path}/{namespace}_{script_name}.apkg"


def package_location():

    # Get the directory of the currently executing script
    current_file = __file__
    return os.path.join(os.path.dirname(os.path.dirname(current_file)), "packages")


def generate(deck, source_file):

    namespace = os.path.basename(os.path.dirname(source_file))
    basename = os.path.basename(source_file)

    print(f"Generating deck {namespace}/{basename}... ")
    genanki.Package(deck).write_to_file(text_to_strings(source_file))