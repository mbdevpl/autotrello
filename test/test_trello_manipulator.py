"""Tests of autotrello.trello_manipulator."""

import os
import unittest

from autotrello.trello_manipulator import TrelloManipulator


class Tests(unittest.TestCase):

    def test_construct(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])

    def test_refresh_boards_list(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()

    def test_set_warmup_board(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_warmup_board('Warm up ⭤')

    def test_set_work_board(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_work_board('Today 🗓')

    def test_set_boards_automatically(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.set_boards_automatically()

    def test_refresh_cache(self):
        trm = TrelloManipulator(api_key=os.environ['AUTOTRELLO_TRELLO_API_KEY'],
                                token=os.environ['AUTOTRELLO_TRELLO_TOKEN'])
        trm.refresh_boards_list()
        trm.set_warmup_board('Warm up ⭤')
        trm.set_work_board('Today 🗓')
        trm.set_handled_normal_boards(['autotrello ⭲'])
        trm.refresh_cache()
