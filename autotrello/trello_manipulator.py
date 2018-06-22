
# import collections
import itertools
import logging
import typing as t

import trello  # py-trello package

from .board_cache import BoardKind, BOARD_SYMBOLS, BOARD_LISTS, BoardCache
from .recurring_board_cache import RecurringBoardCache

_LOG = logging.getLogger(__name__)

_MANIPULATOR_SYMBOL = '⚙'


class TrelloManipulator(trello.TrelloClient):

    """Client for Trello with high-level functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._warmup_board = None
        self._work_board = None
        self._cache = False
        self._boards = None
        self._boards_by_id = None
        self._boards_normal = []
        self._boards_recurring = []

    @property
    def cache(self) -> bool:
        return self._cache

    @cache.setter
    def cache(self, value: bool):
        self._cache = value

    @property
    def boards(self):
        if not self._cache or self._boards is None:
            self.refresh_boards_list()
        return self._boards

    def refresh_boards_list(self):
        self._boards = self.list_boards()
        self._boards_by_id = {b.id: b for b in self._boards}

    def refresh_handled_boards_cache(self):
        self._warmup_board.refresh_cache()
        self._work_board.refresh_cache()
        for board in self._boards_normal:
            board.refresh_cache()
        for board in self._boards_recurring:
            board.refresh_cache()

    def refresh_cache(self):
        _LOG.info('completely rebuilding cache...')
        self.refresh_boards_list()
        self.refresh_handled_boards_cache()
        _LOG.info('cache was completely rebuilt.')

    def find_all_board_ids(self, param_name: str, param_value: t.Any) -> list:
        return [_.id for _ in self.boards if getattr(_, param_name) == param_value]

    def find_board_id(self, param_name: str, param_value: t.Any) -> str:
        board_ids = self.find_all_board_ids(param_name, param_value)
        assert len(board_ids) == 1, len(board_ids)
        return board_ids[0]

    def create_card_data_for_managed_copy(self, card: trello.Card):
        card_data = {}
        card_data['name'] = '{} {} {} {}'.format(
            _MANIPULATOR_SYMBOL, self._boards_by_id[card.board_id].name, _MANIPULATOR_SYMBOL,
            card.name)
        card_data['desc'] = '{} this is auto-created card linked to {} from board {} {}\n\n{}' \
            .format(_MANIPULATOR_SYMBOL, card.url, self._boards_by_id[card.board_id].url,
                    _MANIPULATOR_SYMBOL, card.description)
        try:
            card_data['due'] = card.due_date.isoformat()
        except:
            pass
        # 'labels': []
        # 'position': 'bottom'
        return card_data

    def set_warmup_board(self, name: str) -> None:
        board_id = self.find_board_id('name', name)
        board = BoardCache(self.get_board(board_id), BoardKind.Warmup)
        self._warmup_board = board
        _LOG.info('set warmup board to %s', board)

    def set_work_board(self, name: str) -> None:
        board_id = self.find_board_id('name', name)
        board = BoardCache(self.get_board(board_id), BoardKind.Work)
        self._work_board = board
        _LOG.info('set Work board to %s', board)

    def set_handled_normal_boards(self, board_names: t.Iterable[str]) -> None:
        boards = []
        for name in board_names:
            board_id = self.find_board_id('name', name)
            board = BoardCache(self.get_board(board_id), BoardKind.Normal)
            boards.append(board)
            _LOG.info('set handled normal board %s', board)
        self._boards_normal = boards

    def set_handled_recurring_boards(self, board_names: t.Iterable[str]) -> None:
        boards = []
        for name in board_names:
            board_id = self.find_board_id('name', name)
            board = RecurringBoardCache(self.get_board(board_id), BoardKind.Recurring)
            boards.append(board)
            _LOG.info('set handled recurring board %s', board)
        self._boards_recurring = boards

    def set_boards_automatically(self) -> None:
        self.refresh_boards_list()
        normal_boards: t.List[str] = []
        recurring_boards: t.List[str] = []
        for board in self.boards:
            if board.name.endswith(BOARD_SYMBOLS[BoardKind.Warmup]):
                self.set_warmup_board(board.name)
            elif board.name.endswith(BOARD_SYMBOLS[BoardKind.Work]):
                self.set_work_board(board.name)
            elif board.name.endswith(BOARD_SYMBOLS[BoardKind.Normal]):
                normal_boards.append(board.name)
            elif board.name.endswith(BOARD_SYMBOLS[BoardKind.Recurring]):
                recurring_boards.append(board.name)
        self.set_handled_normal_boards(normal_boards)
        self.set_handled_recurring_boards(recurring_boards)

    def start_warmup(self) -> None:
        """Start warmup."""
        _LOG.info('starting warmup...')
        # create a list of card names being worked on
        self._work_board.refresh_cache()
        cards_being_worked_on = {card.name for card in self._work_board.cached_cards['Doing']}

        self._warmup_board.refresh_cache()
        for list_name in BOARD_LISTS[BoardKind.Warmup]:
            assert not self._warmup_board.cached_cards[list_name], list_name
        # for list_name, cards in self._warmup_board.cached_cards.items():
        #    if list_name == 'Backlog':
        #        _LOG.info('%i cards in backlog', len(cards))
        #        _LOG.debug('cards in backlog: %s', cards)
        #        continue
        #    if len(cards) > 0:
        #        _LOG.error('cannot start my day: cards in %s in list %s.',
        #                   self._startmyday_board, list_name)
        #        raise RuntimeError()

        for board in self._boards_recurring:
            _LOG.info('organizing recurring board %s', board)
            board.organize_cards()

        # add cards from normal boards and recurring boards
        for board in itertools.chain(self._boards_normal, self._boards_recurring):
            _LOG.info('scanning normal board %s', board)
            for card in board.cached_cards['To do']:
                card_data = self.create_card_data_for_managed_copy(card)
                if card_data['name'] in cards_being_worked_on:
                    list_name = 'Now'
                else:
                    list_name = '?'
                _LOG.info('creating card: "%s" in list "%s"', card_data['name'], list_name)
                _LOG.debug('created card data: %s', card_data)
                self._warmup_board.cached_lists[list_name].add_card(**card_data)
        _LOG.info('started warmup.')

    def abort_warmup(self) -> None:
        """Abort warm up session if it is ongoing, do nothing otherwise."""
        if self._warmup_board is None:
            return
        self._warmup_board.refresh_cache()
        for list_name in BOARD_LISTS[BoardKind.Warmup]:
            for card in self._warmup_board.cached_cards[list_name]:
                assert card.name.startswith(_MANIPULATOR_SYMBOL), card
                _LOG.warning('deleting card %s', card)
                card.delete()

    def start_work(self) -> None:
        """Start work, assuming that all cards in warmup are properly classified."""
        _LOG.info('starting work...')
        self._warmup_board.refresh_cache()
        # cannot start work if some tasks are not moved from ? into Now/Later/Never
        if self._warmup_board.cached_cards['?']:
            raise ValueError('List "?" on warmup board has {} cards left, please move them.'.format(
                len(self._warmup_board.cached_cards['?'])))
        self._work_board.refresh_cache()
        cards_being_worked_on = {card.name for card in self._work_board.cached_cards['Doing']}
        self.abort_work()
        # for list_name in BOARD_LISTS[BoardKind.Work]:
        #    if self._work_board.cached_cards[list_name]:
        #        raise ValueError(
        #            'List "{}" on work board has {} cards left, please abort work.'.format(
        #                list_name, len(self._warmup_board.cached_cards[list_name])))
        # delete auto-generated cards that are classified as Later
        for card in self._warmup_board.cached_cards['Later']:
            assert card.name.startswith(_MANIPULATOR_SYMBOL), card
            _LOG.warning('deleting card %s', card)
            card.delete()
        # delete auto-generated cards that are classified as Never
        # for card in self._warmup_board.cached_cards['Never']:
        #    assert card.name.startswith(_MANIPULATOR_SYMBOL), card
        #    _LOG.warning('deleting card %s', card)
        #    card.delete()
        # add Doing cards from normal boards
        for board in self._boards_normal:
            for card in board.cached_cards['Doing']:
                card_data = self.create_card_data_for_managed_copy(card)
                if card_data['name'] in cards_being_worked_on:
                    list_name = 'Doing'
                else:
                    list_name = 'To do'
                _LOG.info('creating card: "%s" in list "%s"', card_data['name'], list_name)
                _LOG.debug('created card data: %s', card_data)
                self._work_board.cached_lists[list_name].add_card(**card_data)
        # move cards classified as Now
        for card in self._warmup_board.cached_cards['Now']:
            assert card.name.startswith(_MANIPULATOR_SYMBOL), card
            _LOG.info('moving card %s to board %s', card, self._work_board)
            if card.name in cards_being_worked_on:
                list_name = 'Doing'
            else:
                list_name = 'To do'
            card.change_board(self._work_board.id, self._work_board.cached_lists[list_name].id)
        # _LOG.info('list %s has %i cards', list_name, len(cards))
        # _LOG.debug('list %s has cards: %s', list_name, cards)
        _LOG.info('work started.')

    def abort_work(self) -> None:
        """Abort today work if it is ongoing, do nothing otherwise."""
        if self._work_board is None:
            return
        self._work_board.refresh_cache()
        for list_name in BOARD_LISTS[BoardKind.Work]:
            for card in self._work_board.cached_cards[list_name]:
                assert card.name.startswith(_MANIPULATOR_SYMBOL), card
                _LOG.warning('deleting card %s', card)
                card.delete()

    def end_work(self):
        _LOG.info('ending work...')
        self._work_board.refresh_cache()
        # for list_name, cards in self._startmyday_board.cached_cards.items():
        #    if list_name != '?':
        #        continue
        #    _LOG.info('list %s has %i cards', list_name, len(cards))
        #    _LOG.debug('list %s has cards: %s', list_name, cards)
        #    for card in cards:
        #        assert card.name.startswith(_MANIPULATOR_SYMBOL), card
        #        _LOG.warning('deleting card %s', card)
        #        card.delete()
        self.abort_work()
        _LOG.info('work ended.')
