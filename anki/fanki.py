import hashlib
import inspect
import json
import os
from abc import abstractmethod
import genanki
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from anki.utilities import text_to_ogg
from bs4 import BeautifulSoup


class FankiModel:

    def __init__(self, model_name, model_id):
        self.name = model_name
        self.id = model_id
        self.fields = []
        self.templates = []
        self.css = ""
        self._root_path = None

    def add_field(self, name):
        self.fields.append({'name': name})

    def get_fields(self):
        return self.fields

    def add_template(self, name, question_format, answer_format):
        self.templates.append({
            'name': name,
            'qfmt': question_format,
            'afmt': answer_format,
        })


    def get_templates(self):
        return self.templates


    def set_css(self, css):
        self.css = css

    def get_css(self):
        return self.css

    def get_model(self):

        return genanki.Model(self.id, self.name, fields=self.get_fields(), templates=self.get_templates(), css=self.get_css())




def _get_real_file_path(file_path):
    __dir__ = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(__dir__, "models", file_path)


def _get_file_content(file_path) ->str:
    file_real_path = _get_real_file_path(file_path)

    #if file exist
    if os.path.isfile(file_real_path):
        with open(file_real_path, 'r') as file:
            return file.read()
    else:
        return ""

class FankiModelGeneric:

    def __init__(self, deck_id=None, deck_name=None, deck_namespace=None, deck_alias=None, root_path=None):

        caller_file_path = inspect.stack()[1].filename
        caller_dir_path = os.path.dirname(os.path.realpath(caller_file_path))

        if root_path is None or not os.path.isdir(root_path):
            root_path = caller_dir_path

        self._valid_audio_files = [".mp3", ".ogg", ".wav", ".flac", ".m4a"]
        self._valid_image_files = [".jpg", ".png", ".gif", ".tiff", ".svg", ".tif", ".jpeg", ".webp"]
        self._valid_video_files = [".avi", ".ogv", ".mpg", ".mpeg", ".mov", ".mp4", ".mkv", ".flv", ".swf"]
        self._valid_any_files = self._valid_audio_files + self._valid_image_files + self._valid_video_files

        self._root_path = root_path
        self._path_assets = os.path.join(self._root_path, "assets")

        if not os.path.isdir(self._root_path):
            raise FileNotFoundError(f"_root_path folder ({self._root_path}) not found")

        if not os.path.isdir(self._path_assets):
            raise FileNotFoundError(f"_path_assets folder ({self._path_assets}) not found")


        self._deck_id = int(deck_id)
        self._deck_name = deck_name
        self._deck_alias = deck_alias
        self._deck_namespace = deck_namespace

        if self._deck_id is None or not isinstance(self._deck_id, int) or self._deck_id < 0:
            raise ValueError("deck_id is required")

        if self._deck_name is None:
            raise ValueError("deck_name is required")

        if self._deck_alias is None:
            raise ValueError("deck_alias is required")

        if self._deck_namespace is None:
            raise ValueError("deck_namespace is required")


        self._packages_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "packages")
        self._temp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "temp")

        if not os.path.isdir(self._packages_path):
            raise FileNotFoundError(f"_packages_path folder ({self._packages_path}) not found")

        if not os.path.isdir(self._temp_path):
            raise FileNotFoundError(f"_temp_path folder ({self._temp_path}) not found")

        self._deck_cards = []
        self._deck_media = []
        self._f_model = self._f_model_instance()
        self._setup()

    @abstractmethod
    def _setup(self):
        pass


    @abstractmethod
    def _f_model_instance(self) -> FankiModel:

        pass

    @abstractmethod
    def import_cards(self, data):

        pass

    def _get_model_instance(self) -> genanki.Model:

        return self._f_model.get_model()

    def _get_deck_instance(self) -> genanki.Deck:

        model = self._get_model_instance()
        deck = genanki.Deck(self._deck_id, self._deck_name)

        model_fields = [field['name'] for field in self._f_model.get_fields()]

        for card in self._deck_cards:
            card = self._parse_card_fields(card)

            fields = [card.get(field_name) if card.get(field_name) is not None else "" for field_name in model_fields]
            print(fields)


            note = genanki.Note(model=model, fields=fields)
            deck.add_note(note)

        return deck

    def _parse_card_fields(self, card) -> dict:

        # special fields
        for field_name, field_value in card.items():
            card[field_name] = self._parse_field_value(field_name, field_value)

        # tts fields
        for field_name, field_value in card.items():
            card[field_name] = self._parse_field_value_tts(card, field_name, field_value)

        for field_name, field_value in card.items():
            if not isinstance(field_value, str):
                card[field_name] = ""

        return card


    def _parse_field_value(self, field_name, field_value) -> str:

        if field_name.endswith("_tts"):
            return field_value

        if field_value is None:
            return ""


        is_image = any([field_value.endswith(valid_file) for valid_file in self._valid_image_files])
        is_audio = any([field_value.endswith(valid_file) for valid_file in self._valid_audio_files])
        is_video = any([field_value.endswith(valid_file) for valid_file in self._valid_video_files])
        is_file = any([field_value.endswith(valid_file) for valid_file in self._valid_any_files])
        asset_path = self._asset_exists(field_value)

        if not is_file or not field_value.startswith("assets/") or self._root_path is None or asset_path is None:
            return field_value

        if is_audio and field_name.endswith("_audio"):
            file_path = self._convert_to_ogg(asset_path)
            self._deck_media.append(file_path)
            return "[sound:{}]".format(os.path.basename(file_path))

        if is_video and field_name.endswith("_video"):
            file_path = self._convert_to_mp4(asset_path)
            self._deck_media.append(file_path)
            return os.path.basename(file_path)

        if is_image:
            file_path = self._convert_to_webp(asset_path)
            self._deck_media.append(file_path)
            return '<img src="' + os.path.basename(file_path) + '">'

        return field_value

    def _parse_field_value_tts(self, card, field_name, field_value):

        if not field_name.endswith("_tts"):
            return field_value

        field_name_base = field_name[:-4]
        field_name_audio = field_name_base + "_audio"

        if card.get(field_name_audio):
            return None

        if field_value is True and not card.get(field_name_base):
            return None

        if field_value is True:

            field_value = card.get(field_name_base)

            if "<" in field_value:
                field_value = BeautifulSoup(field_value, "html.parser").get_text()

        if not isinstance(field_value, str) or field_value == "":
            return None

        # md5 field_value as string
        md5 = hashlib.md5(field_value.encode()).hexdigest()
        file_name = f"tts_{md5}.ogg"
        file_path = os.path.join(self._path_assets, file_name)

        if not os.path.isfile(file_path):
            file_path = text_to_ogg(text=field_value, destination_path=file_path, prosody='slow')
            print(file_path)

        if not os.path.isfile(file_path):
            return None

        self._deck_media.append(file_path)

        card[field_name_audio] = "[sound:{}]".format(os.path.basename(file_path))

        return None

    def _copy_asset(self, _asset_path):

        if not os.path.isfile(_asset_path):
            raise FileNotFoundError("{} is not a file", _asset_path)

        temp_file_path = self._temp_asset_path(_asset_path)
        os.system(f"cp {_asset_path} {temp_file_path}")
        return temp_file_path

    def _temp_asset_path(self, _asset_path):
        return self._asset_temp_path(self._asset_final_name(_asset_path))

    def _convert_to_webp(self, asset_path):

        if asset_path.endswith(".webp"):
            return self._copy_asset(asset_path)

        temp_file_path = self._temp_asset_path(asset_path)

        temp_file_path = os.path.splitext(temp_file_path)[0] + ".webp"

        image = Image.open(asset_path)
        image.save(temp_file_path, 'webp')
        return temp_file_path

    def _convert_to_ogg(self, asset_path):

        if asset_path.endswith(".ogg"):
            return self._copy_asset(asset_path)

        temp_file_path = self._temp_asset_path(asset_path)
        temp_file_path = os.path.splitext(temp_file_path)[0] + ".ogg"

        audio = AudioSegment.from_file(asset_path)
        audio.export(temp_file_path, format="ogg")
        return temp_file_path

    def _convert_to_mp4(self, asset_path):

        if asset_path.endswith(".mp4"):
            return self._copy_asset(asset_path)

        temp_file_path = self._temp_asset_path(asset_path)
        temp_file_path = os.path.splitext(temp_file_path)[0] + ".mp4"

        clip = VideoFileClip(asset_path)
        clip.write_videofile(temp_file_path, codec='libx264')

        return temp_file_path


    def _asset_temp_path(self, file_name):

        # if self._temp_path is None or folder not exist
        if self._temp_path is None:
            raise ValueError("temp_path is required")

        if not os.path.isdir(self._temp_path):
            raise FileNotFoundError("{} is not a directory", self._temp_path)

        temp_path = os.path.join(self._temp_path, self._deck_namespace + "." + self._deck_alias)
        temp_path_full = os.path.join(temp_path, os.path.basename(file_name))
        if not os.path.isdir(temp_path):
            os.makedirs(temp_path)


        # if file exist, delete it
        if os.path.isfile(temp_path_full):
            os.remove(temp_path_full)

        return temp_path_full


    def _asset_exists(self, file_name):

        if not file_name.startswith("assets/"):
            return None

        if self._root_path is None:
            return None
        file_path = os.path.join(self._root_path, file_name)
        if os.path.isfile(_get_real_file_path(file_path)):
            return file_path
        return None

    def _asset_final_name(self, file_name):

        if file_name.startswith("assets/"):
            return file_name[7:]
        return file_name

    @classmethod
    def import_deck(cls, data_file_path=None):


        if data_file_path is None or not os.path.isdir(data_file_path):
            caller_file_path = inspect.stack()[1].filename
            data_file_path = os.path.dirname(os.path.realpath(caller_file_path))


        if not os.path.isdir(data_file_path):
            raise FileNotFoundError("data_file is required")

        alias = os.path.basename(data_file_path)
        namespace = os.path.basename(os.path.dirname(data_file_path))
        json_file_path = os.path.join(data_file_path,  "data.json")

        if not os.path.isfile(json_file_path):
            raise FileNotFoundError("File {} not found".format(json_file_path))

        with open(json_file_path, 'r') as file:
            json_content = file.read()
            # import json content
            data = json.loads(json_content)

            deck_id = data.get('id')
            deck_name = data.get('name')
            deck_namespace = namespace
            deck_alias = alias
            deck_cards = data.get('cards')

            if deck_id is None:
                raise ValueError("deck_id is required")
            if deck_name is None:
                raise ValueError("deck_name is required")
            if deck_namespace is None:
                raise ValueError("deck_namespace is required")
            if deck_alias is None:
                raise ValueError("deck_alias is required")
            if (deck_cards is None) or (len(deck_cards) == 0):
                raise ValueError("cards is required")

            deck = cls(
                deck_id=int(deck_id),
                deck_name=deck_name,
                deck_namespace=deck_namespace,
                deck_alias=deck_alias,
                root_path=data_file_path
            )
            deck.import_cards(deck_cards)

            return deck

        pass

    def generate(self):

        if self._root_path is None:
            raise ValueError("root_path is required")

        anki_package = genanki.Package(self._get_deck_instance())

        if len(self._deck_media) > 0:
            anki_package.media_files = self._deck_media

        # remove all .apkg files in self._root_path directory
        for file in os.listdir(self._root_path):
            if file.endswith(".apkg"):
                os.remove(os.path.join(self._root_path, file))

        #dest_file = os.path.join(self._root_path, "package.apkg")
        #anki_package.write_to_file(dest_file)

        dest_file = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "packages", f"{self._deck_namespace}_{self._deck_alias}.apkg")
        anki_package.write_to_file(dest_file)


    def set_root_paht(self, caller_dir_path):
        self._root_path = caller_dir_path
        pass


class FankiModelDefault(FankiModelGeneric):

    def _f_model_instance(self) -> FankiModel:
        return FankiModel('FM Default', 1607392319)

    def _setup(self):


        self._f_model.add_template("Card1", _get_file_content("default/front.html"), _get_file_content("default/back.html"))
        self._f_model.set_css(_get_file_content("default/style.css"))

        self._f_model.add_field('front')
        self._f_model.add_field('front_image')
        self._f_model.add_field('front_audio')
        self._f_model.add_field('back')
        self._f_model.add_field('back_image')
        self._f_model.add_field('back_audio')
        self._f_model.add_field('back_sentence')
        self._f_model.add_field('back_sentence_audio')
        self._f_model.add_field('back_ipa')

    def add_card(self, front=None, front_image=None, front_audio=None, back=None, back_tts=None, back_image=None, back_audio=None, back_sentence=None, back_sentence_tts=None, back_sentence_audio=None, ipa=None):

        self._deck_cards.append({
            'front': front,
            'front_image': front_image,
            'front_audio': front_audio,
            'back': back,
            'back_tts': back,
            'back_image': back_image,
            'back_audio': back_audio,
            'back_sentence': back_sentence,
            'back_sentence_tts': back_sentence_tts,
            'back_sentence_audio': back_sentence_audio,
            'back_ipa': ipa
        })

    def import_cards(self, data):

        for card in data:

            self.add_card(
                front=card.get('front'),
                front_image=card.get('front_image'),
                front_audio=card.get('front_audio'),
                back=card.get('back'),
                back_tts=card.get('back_tts'),
                back_image=card.get('back_image'),
                back_audio=card.get('back_audio'),
                back_sentence=card.get('back_sentence'),
                back_sentence_tts=card.get('back_sentence_tts'),
                back_sentence_audio=card.get('back_sentence_audio'),
                ipa=card.get('back_ipa')
            )

