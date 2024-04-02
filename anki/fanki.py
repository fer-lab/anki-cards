import inspect
import json
import os
from abc import abstractmethod

import genanki


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

    def __init__(self, deck_id, deck_name, deck_namespace, deck_alias):

        self._deck_id = deck_id
        self._deck_name = deck_name
        self._deck_alias = deck_alias
        self._deck_namespace = deck_namespace

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

        field_names = [field['name'] for field in self._f_model.get_fields()]


        for card in self._deck_cards:

            fields = [self._parse_file(card.get(field_name)) for field_name in field_names]
            note = genanki.Note(model=model, fields=fields)

            deck.add_note(note)

        return deck

        pass

    def _parse_file(self, field_value) -> str:
        if field_value is None:
            return ""

        valid_audio_files = [".mp3", ".wav"]
        valid_image_files = [".jpg", ".jpeg", ".png", ".gif"]
        valid_files = valid_audio_files + valid_image_files
        is_image = any([field_value.endswith(valid_file) for valid_file in valid_image_files])
        is_audio = any([field_value.endswith(valid_file) for valid_file in valid_audio_files])
        is_file = any([field_value.endswith(valid_file) for valid_file in valid_files])
        asset_path = self._asset_exists(field_value)

        if not is_file or not field_value.startswith("assets/") or self._root_path is None or asset_path is None:
            return field_value

        if is_audio:
            self._deck_media.append(asset_path)
            return '<audio src="' + os.path.basename(asset_path) + '">'

        if is_image:
            self._deck_media.append(asset_path)
            return '<img src="' + os.path.basename(asset_path) + '">'

        return field_value

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
    def import_deck(cls):

        caller_file_path = inspect.stack()[1].filename
        caller_dir_path = os.path.dirname(os.path.realpath(caller_file_path))
        alias = os.path.basename(os.path.dirname(caller_file_path))
        namespace = os.path.basename(os.path.dirname(os.path.dirname(caller_file_path)))
        json_file_path = os.path.join(caller_dir_path,  "data.json")


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

            deck = cls(int(deck_id), deck_name, deck_namespace, deck_alias)
            deck.set_root_paht(caller_dir_path)
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

    def add_card(self, front=None, front_image=None, front_audio=None, back=None, back_image=None, back_audio=None, back_sentence=None, back_sentence_audio=None, ipa=None):

        self._deck_cards.append({
            'front': front,
            'front_image': front_image,
            'front_audio': front_audio,
            'back': back,
            'back_image': back_image,
            'back_audio': back_audio,
            'back_sentence': back_sentence,
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
                back_image=card.get('back_image'),
                back_audio=card.get('back_audio'),
                back_sentence=card.get('back_sentence'),
                back_sentence_audio=card.get('back_sentence_audio'),
                ipa=card.get('back_ipa')
            )

