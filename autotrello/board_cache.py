
import collections
import enum
import logging
import typing as t

import trello  # py-trello package

_LOG = logging.getLogger(__name__)


@enum.unique
class BoardKind(enum.Enum):

    """Available kinds of boards."""

    Warmup = 1 + 4
    Work = 1 + 8
    Normal = 2 + 16
    Recurring = 2 + 32


BOARD_SYMBOLS = {
    BoardKind.Warmup: '⭤',
    BoardKind.Work: '🗓',
    BoardKind.Normal: '⭲',
    BoardKind.Recurring: '⭮'}


BOARD_LISTS = {
    BoardKind.Warmup: ['?', 'Now', 'Later'],
    BoardKind.Work: ['To do', 'Doing', 'Done', 'Not today'],
    BoardKind.Normal: ['To do', 'Doing'],
    BoardKind.Recurring: ['To do', 'Done']}


class BoardCache:

    """Wrapper around trello.Board that caches all downloaded data."""

    def __init__(self, board: trello.Board, board_kind: BoardKind, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._board = board
        self._board_kind = board_kind
        self._lists = None
        self._list_cards = None
        self._refresh()
        # assert all([_ in self._lists for _ in BOARD_LISTS[self._board_kind]]),
        #    (board, board.cached_lists)

    @property
    def cached_lists(self) -> t.Mapping[str, trello.List]:
        return self._lists

    @property
    def cached_cards(self) -> t.Mapping[str, t.Sequence[trello.Card]]:
        return self._list_cards

    def cached_list(self, name: str) -> trello.List:
        return self._lists[name]

    def cached_list_cards(self, name: str) -> t.Sequence[trello.Card]:
        return self._list_cards[name]

    def refresh_cache(self):
        self._refresh()

    def _refresh(self):
        if not self._board.name.endswith(BOARD_SYMBOLS[self._board_kind]):
            raise ValueError(
                'Board "{}" is invalid: name of board of kind {} should end with {}.'
                .format(self._board.name, self._board_kind, BOARD_SYMBOLS[self._board_kind]))
        self._lists = collections.OrderedDict()
        self._list_cards = collections.OrderedDict()
        for board_list in self._board.all_lists():
            name = board_list.name
            if name not in BOARD_LISTS[self._board_kind]:
                continue
            self._lists[name] = board_list
            self._list_cards[name] = board_list.list_cards()
        for list_name in BOARD_LISTS[self._board_kind]:
            if list_name not in self._lists:
                raise ValueError('Board "{}" is invalid: board of kind {} should contain list "{}".'
                                 .format(self._board.name, self._board_kind, list_name))

    def __getattr__(self, name):
        return getattr(self._board, name)

    def __repr__(self):
        return repr(self._board)

    def __str__(self):
        return str(self._board)
