import unittest
import sys
from unittest.mock import MagicMock

# Mock dependencies before importing the module
sys.modules["psycopg"] = MagicMock()
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Now we can import the module
from toelo.player_elo.database_connection import get_connection_string

class TestDatabaseConnection(unittest.TestCase):
    def test_get_connection_string(self):
        config = {
            "dbname": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "test_host",
            "port": "5432",
        }
        expected = "postgresql+psycopg://test_user:test_password@test_host:5432/test_db"
        self.assertEqual(get_connection_string(config), expected)

if __name__ == "__main__":
    unittest.main()
