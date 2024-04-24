import random
import boto3
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


def text_to_ogg(lang='fr', text="", destination_path=None, prosody=False) -> str:

    voices = {
        'fr': ['Lea', 'Remi'],
        'en': ['Matthew', 'Joanna']
    }

    # if lang exist in voices
    if lang not in voices:
        raise ValueError("lang must exist in voices")

    if destination_path is None:
        raise ValueError("destination_path must be specified")

    if text == "" or not isinstance(text, str):
        raise ValueError("text must be specified")

    session = boto3.Session(profile_name='fer', region_name='us-east-1')
    polly_client = session.client('polly')

    # get rando voice from voices
    voice = random.choice(voices[lang])

    response = polly_client.synthesize_speech(
        Engine='neural',
        VoiceId=voice,
        OutputFormat='ogg_vorbis',
        Text=f'<speak><prosody rate="{prosody}">{text}</prosody></speak>' if prosody else text,
        TextType='ssml' if prosody else 'text'
    )

    with open(destination_path, 'wb') as file:
        file.write(response['AudioStream'].read())

    return destination_path

def package_location():

    # Get the directory of the currently executing script
    current_file = __file__
    return os.path.join(os.path.dirname(os.path.dirname(current_file)), "packages")


def generate(deck, source_file):

    namespace = os.path.basename(os.path.dirname(source_file))
    basename = os.path.basename(source_file)

    print(f"Generating deck {namespace}/{basename}... ")
    genanki.Package(deck).write_to_file(text_to_strings(source_file))