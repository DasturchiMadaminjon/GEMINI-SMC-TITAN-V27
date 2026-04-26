import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import DatabaseManager

class TestDatabase:
    @patch('utils.database.sqlite3')
    def test_database_initialization(self, mock_sqlite3):
        # Prevent it from actually creating dirs/files
        with patch('os.makedirs'):
            db = DatabaseManager(db_path=':memory:')
            assert db is not None
