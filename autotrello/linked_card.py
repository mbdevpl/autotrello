
import trello  # py-trello package


class LinkedCard:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card: trello.Card = None
