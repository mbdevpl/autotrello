"""Tests of autotrello.trello_manipulator."""

import os
import unittest

from autotrello.trello_manipulator import TrelloManipulator


class Tests(unittest.TestCase):

    def test_construct(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        self.assertIsInstance(trm, TrelloManipulator)

    def test_refresh_boards_list(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        self.assertGreater(len(trm.boards), 0)

    def test_set_warmup_board(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_warmup_board('Warm up ⭤')
        self.assertIsNotNone(trm.warmup_board)

    def test_set_work_board(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_work_board('Today 🗓')
        self.assertIsNotNone(trm.work_board)

    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    def test_set_boards_automatically(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.set_boards_automatically()
        self.assertIsNotNone(trm.warmup_board)
        self.assertIsNotNone(trm.work_board)
        self.assertGreater(len(trm.normal_boards), 0)
        self.assertGreater(len(trm.recurring_boards), 0)

    def test_refresh_cache(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_warmup_board('Warm up ⭤')
        trm.set_work_board('Today 🗓')
        trm.set_handled_normal_boards(['autotrello ⭲'])
        self.assertGreater(len(trm.normal_boards), 0)
        self.assertEqual(trm.normal_boards[0].name, 'autotrello ⭲')
        trm.refresh_cache()
        self.assertGreater(len(trm.normal_boards[0].cached_lists), 0)
        self.assertGreater(len(trm.normal_boards[0].cached_cards), 0)

    @unittest.skipUnless(os.environ.get('TEST_LONG'), 'skipping long test')
    def test_full_sync(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.set_boards_automatically()
        self.assertGreater(len(trm.normal_boards), 0)
        self.assertGreater(len(trm.recurring_boards), 0)
        trm.refresh_cache()
