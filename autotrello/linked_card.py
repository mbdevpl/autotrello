"""Trello card linked to another Trello card."""

import trello  # py-trello package


class LinkedCard:  # pylint: disable = too-few-public-methods
    """Trello card linked to another for easy synchronization."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card: trello.Card = None
