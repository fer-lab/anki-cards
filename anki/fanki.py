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

            fields = [card.get(field_name) if card.get(field_name) is not None else '' for field_name in field_names]
            note = genanki.Note(model=model, fields=fields)

            deck.add_note(note)

        return deck

        pass

    @classmethod
    def import_deck(cls):

        caller_file_path = inspect.stack()[1].filename
        caller_dir_path = os.path.dirname(os.path.realpath(caller_file_path))
        alias = os.path.splitext(os.path.basename(caller_file_path))[0]
        namespace = os.path.basename(os.path.dirname(caller_file_path))
        json_file_path = os.path.join(caller_dir_path, alias + ".json")

        if not os.path.isfile(json_file_path):
            raise FileNotFoundError(f"File {json_file_path} not found")

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
            deck.import_cards(deck_cards)

            return deck

        pass

    def generate(self):

        genanki.Package(self._get_deck_instance()).write_to_file(
            os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "packages", f"{self._deck_namespace}_{self._deck_alias}.apkg")
        )


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

