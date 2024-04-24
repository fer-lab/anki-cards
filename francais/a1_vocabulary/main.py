import sys
sys.path.insert(0, '../../')

from anki.fanki import FankiModelDefault

deck = FankiModelDefault.import_deck()
deck.generate()
