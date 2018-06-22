
import datetime
import enum
import itertools
import logging
import math
import typing as t

import trello  # py-trello package
import tzlocal

from .board_cache import BoardCache

WEEK = 7.0
MONTH = 30.4375
YEAR = 365.25


@enum.unique
class Every(enum.Enum):

    """Available frequencies."""

    OneDay = 1
    TwoDays = 2
    ThreeDays = 3
    OneWeek = 7
    TwoWeeks = 14
    ThreeWeeks = 21
    OneMonth = 30
    TwoMonths = 60
    ThreeMonths = 90
    Quarter = 91
    HalfYear = 182
    OneYear = 365
    TwoYears = 731
    ThreeYears = 1096


FREQUENCIES = {
    Every.OneDay: datetime.timedelta(days=1),
    Every.TwoDays: datetime.timedelta(days=2),
    Every.ThreeDays: datetime.timedelta(days=3),
    Every.OneWeek: datetime.timedelta(days=round(1 * WEEK)),
    Every.TwoWeeks: datetime.timedelta(days=round(2 * WEEK)),
    Every.ThreeWeeks: datetime.timedelta(days=round(3 * WEEK)),
    Every.OneMonth: datetime.timedelta(days=round(1 * MONTH)),
    Every.TwoMonths: datetime.timedelta(days=round(2 * MONTH)),
    Every.ThreeMonths: datetime.timedelta(days=round(3 * MONTH)),
    Every.Quarter: datetime.timedelta(days=round(0.25 * YEAR)),
    Every.HalfYear: datetime.timedelta(days=round(0.5 * YEAR)),
    Every.OneYear: datetime.timedelta(days=round(1 * YEAR)),
    Every.TwoYears: datetime.timedelta(days=round(2 * YEAR)),
    Every.ThreeYears: datetime.timedelta(days=round(3 * YEAR))}

REMINDERS = {id_: datetime.timedelta(days=round(math.sqrt(freq.days)))
             for id_, freq in FREQUENCIES.items()}

FREQUENCIES_TRANSLATIONS = {
    'en': {
        'daily': Every.OneDay,
        'weekly': Every.OneWeek,
        'biweekly': Every.TwoWeeks,
        'triweekly': Every.ThreeWeeks,
        'monthly': Every.OneMonth,
        'bimonthly': Every.TwoMonths,
        'trimonthly': Every.ThreeMonths,
        'quarterly': Every.Quarter,
        'semianually': Every.HalfYear,
        'yearly': Every.OneYear,
        'biyearly': Every.TwoYears,
        'triyearly': Every.ThreeYears},
    'pl': {
        'codziennie': Every.OneDay,
        'co 2 dni': Every.TwoDays,
        'co 3 dni': Every.ThreeDays,
        'co tydzień': Every.OneWeek,
        'co 2 tyg.': Every.TwoWeeks,
        'co 3 tyg.': Every.ThreeWeeks,
        'co miesiąc': Every.OneMonth,
        'co 2 mies.': Every.TwoMonths,
        'co 3 mies.': Every.ThreeMonths,
        'co kwartał': Every.Quarter,
        'co pół roku': Every.HalfYear,
        'co rok': Every.OneYear,
        'co 2 lata': Every.TwoYears,
        'co 3 lata': Every.ThreeYears},
    'ja': {
        '毎日': Every.OneDay,
        '隔日': Every.TwoDays,
        '３日毎': Every.ThreeDays,
        '毎週': Every.OneWeek,
        '隔週': Every.TwoWeeks,
        '３週毎': Every.ThreeWeeks,
        '毎月': Every.OneMonth,
        '隔月': Every.TwoMonths,
        '３月毎': Every.ThreeMonths,
        '四半期毎': Every.Quarter,
        '半年毎': Every.HalfYear,
        '毎年': Every.OneYear,
        '隔年': Every.TwoYears,
        '３年毎': Every.ThreeYears}}

FREQUENCIES_MEANINGS = {}
for _, translations in FREQUENCIES_TRANSLATIONS.items():
    FREQUENCIES_MEANINGS.update(translations)

_LOG = logging.getLogger(__name__)


class RecurringBoardCache(BoardCache):

    """A cache for trello.Board capable of automatic card organization based on some assumptions.

    Assumptions:

    1. columns 'To do' and 'Done' exist

    2. all cards in those columns have due dates

    3. names of all cards in those columns start with one of predefined prefixes
    as defined in FREQUENCIES_TRANSLATIONS

    If all conditions are satisfied, auto-organization can happen.

    All cards with near due date are moved to To do, and all cards with not near due date are moved
    to Done.

    Nearness is determined based on frequency and deadline information,
    formula given by FREQUENCIES and REMINDERS variables and _refresh() method.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._now = None
        self._soon: t.List[trello.Card] = []
        self._not_soon: t.List[trello.Card] = []

    def _refresh(self):
        super()._refresh()
        local = tzlocal.get_localzone()
        self._now = datetime.datetime.now(local)

        invalid = []
        self._soon = []
        self._not_soon = []
        for card in itertools.chain(self.cached_cards['To do'], self.cached_cards['Done']):
            if not card.due_date:
                _LOG.warning('skipping card %s: no due date!', card)
                invalid.append(card)
                continue
            if ':' in card.name:
                card_frequency_str = card.name.partition(':')[0]
                if card_frequency_str not in FREQUENCIES_MEANINGS:
                    _LOG.warning('skipping card %s: frequency "%s" unrecognized!',
                                 card, card_frequency_str)
                    invalid.append(card)
                    continue
            else:
                _LOG.warning('skipping card %s: no frequency information!', card)
                invalid.append(card)
                continue
            if card.due_date - REMINDERS[FREQUENCIES_MEANINGS[card_frequency_str]] <= self._now:
                self._soon.append(card)
            else:
                self._not_soon.append(card)
        if invalid:
            raise ValueError('Following cards are invalid for recurring board: {}'.format(
                [card.name for card in invalid]))
        self._soon = sorted(self._soon, key=lambda x: x.due_date)
        self._not_soon = sorted(self._not_soon, key=lambda x: x.due_date)

    def organize_cards(self):
        todo_list = self.cached_lists['To do']
        done_list = self.cached_lists['Done']
        moved_to_todo = False
        for card in self._soon:
            if card.list_id == todo_list.id:
                continue
            _LOG.warning('moving card %s to %s', card, todo_list)
            card.change_list(todo_list.id)
            moved_to_todo = True
        moved_to_done = False
        for card in self._not_soon:
            if card.list_id == done_list.id:
                continue
            _LOG.warning('moving card %s to %s', card, done_list)
            card.change_list(done_list.id)
            moved_to_done = True
        if moved_to_todo:
            _LOG.warning('sorting cards in %s', todo_list)
            for card in reversed(self._soon):
                card.change_pos('top')
        if moved_to_done:
            _LOG.warning('sorting cards in %s', done_list)
            for card in reversed(self._not_soon):
                card.change_pos('top')
        if moved_to_todo or moved_to_done:
            self._refresh()
