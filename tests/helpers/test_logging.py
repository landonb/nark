# -*- encoding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging

from hamster_lib.helpers import logging as logging_helpers


class TestSetupHandler(object):
    def test_get_formatter_basic(self, mocker):
        """Test formatter fetcher."""
        formatter = logging_helpers.formatter_basic()
        assert 'levelname' in formatter

    def test_setup_handler_stream_handler(self, mocker):
        """Test logging setup."""
        stream_handler = logging.StreamHandler()
        formatter = logging_helpers.formatter_basic()
        logger = mocker.MagicMock()
        logging_helpers.setupHandler(stream_handler, formatter, logger)
        logger.addHandler.assert_called_with(stream_handler)

