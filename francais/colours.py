import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from anki.fanki import FankiModelDefault

deck = FankiModelDefault.import_deck()
deck.generate()
