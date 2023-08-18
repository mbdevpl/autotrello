"""Initialization of tests for autotrello package."""

import logging

import boilerplates.logging


class TestsLogging(boilerplates.logging.Logging):
    """Test logging configuration."""

    packages = ['autotrello']


TestsLogging.configure()
