"""
Test suite for credit card transaction data seeding script
Tests all functions and edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os

# Add parent directory to path to import the script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.seed_credit_card_data import (
    generate_transaction_id,
    generate_transaction,
    seed_database,
    MERCHANTS,
    CARD_NUMBERS,
    CARDHOLDERS,
    TRANSACTION_AMOUNTS,
    LOCATIONS
)


class TestGenerateTransactionId:
    """Test suite for generate_transaction_id function"""

    def test_single_digit_id(self):
        """Test transaction ID generation for single digit"""
        result = generate_transaction_id(1)
        assert result == "TXN000001"

    def test_double_digit_id(self):
        """Test transaction ID generation for double digit"""
        result = generate_transaction_id(42)
        assert result == "TXN000042"

    def test_large_id(self):
        """Test transaction ID generation for large numbers"""
        result = generate_transaction_id(123456)
        assert result == "TXN123456"

    def test_zero_id(self):
        """Test transaction ID generation for zero"""
        result = generate_transaction_id(0)
        assert result == "TXN000000"

    def test_id_format(self):
        """Test that ID follows correct format"""
        result = generate_transaction_id(999)
        assert result.startswith("TXN")
        assert len(result) == 9
        assert result[3:].isdigit()


class TestGenerateTransaction:
    """Test suite for generate_transaction function"""

    def test_transaction_structure(self):
        """Test that generated transaction has all required fields"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)

        required_fields = [
            "transaction_id", "card_number", "cardholder_name",
            "transaction_date", "post_date", "merchant_name",
            "category", "amount", "currency", "transaction_type",
            "status", "description", "location", "is_international",
            "rewards_earned"
        ]

        for field in required_fields:
            assert field in transaction, f"Missing field: {field}"

    def test_transaction_id_format(self):
        """Test transaction ID is correctly formatted"""
        base_date = datetime.now()
        transaction = generate_transaction(5, base_date)
        assert transaction["transaction_id"] == "TXN000005"

    def test_category_valid(self):
        """Test that category is from valid merchant categories"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction["category"] in MERCHANTS.keys()

    def test_merchant_matches_category(self):
        """Test that merchant belongs to selected category"""
        base_date = datetime.now()
        for i in range(10):
            transaction = generate_transaction(i, base_date)
            category = transaction["category"]
            merchant = transaction["merchant_name"]
            assert merchant in MERCHANTS[category]

    def test_amount_within_category_range(self):
        """Test that amount is within category's expected range"""
        base_date = datetime.now()
        for i in range(20):
            transaction = generate_transaction(i, base_date)
            category = transaction["category"]
            amount = abs(transaction["amount"])
            min_amt, max_amt = TRANSACTION_AMOUNTS[category]
            assert min_amt <= amount <= max_amt

    def test_currency_is_usd(self):
        """Test that currency is always USD"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction["currency"] == "USD"

    def test_post_date_after_transaction_date(self):
        """Test that post date is after transaction date"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction["post_date"] >= transaction["transaction_date"]

    def test_transaction_date_in_past(self):
        """Test that transaction date is in the past 90 days"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        days_diff = (base_date - transaction["transaction_date"]).days
        assert 0 <= days_diff <= 90

    def test_card_number_valid(self):
        """Test that card number is from valid list"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction["card_number"] in CARD_NUMBERS

    def test_cardholder_name_valid(self):
        """Test that cardholder name is from valid list"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction["cardholder_name"] in CARDHOLDERS

    def test_card_number_matches_cardholder(self):
        """Test that card number corresponds to correct cardholder"""
        base_date = datetime.now()
        for i in range(20):
            transaction = generate_transaction(i, base_date)
            cardholder_idx = CARDHOLDERS.index(transaction["cardholder_name"])
            assert transaction["card_number"] == CARD_NUMBERS[cardholder_idx]

    def test_transaction_type_valid(self):
        """Test that transaction type is valid"""
        base_date = datetime.now()
        valid_types = ["purchase", "refund", "payment", "fee", "interest", "cashback"]
        for i in range(50):
            transaction = generate_transaction(i, base_date)
            assert transaction["transaction_type"] in valid_types

    def test_status_valid(self):
        """Test that status is valid"""
        base_date = datetime.now()
        valid_statuses = ["posted", "pending", "declined", "reversed"]
        for i in range(50):
            transaction = generate_transaction(i, base_date)
            assert transaction["status"] in valid_statuses

    def test_refund_has_negative_amount(self):
        """Test that refunds, payments, and cashbacks have negative amounts"""
        base_date = datetime.now()
        # Run multiple times to catch these transaction types
        refund_found = False
        for i in range(100):
            transaction = generate_transaction(i, base_date)
            if transaction["transaction_type"] in ["refund", "payment", "cashback"]:
                assert transaction["amount"] < 0
                refund_found = True
        # Note: Due to randomness, we might not always find these types

    def test_location_structure(self):
        """Test that location has required fields"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        location = transaction["location"]
        assert "city" in location
        assert "state" in location
        assert "country" in location

    def test_description_format(self):
        """Test that description includes transaction type and merchant"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        description = transaction["description"]
        assert transaction["transaction_type"].title() in description
        assert transaction["merchant_name"] in description
        assert transaction["category"].title() in description

    def test_rewards_calculation_purchase(self):
        """Test rewards calculation for purchases"""
        base_date = datetime.now()
        # Find a posted purchase transaction
        for i in range(100):
            transaction = generate_transaction(i, base_date)
            if (transaction["transaction_type"] == "purchase" and
                transaction["status"] == "posted"):
                category = transaction["category"]
                amount = abs(transaction["amount"])
                expected_rate = 0.01
                if category == "dining":
                    expected_rate = 0.02
                elif category == "travel":
                    expected_rate = 0.03

                expected_rewards = round(amount * expected_rate, 2)
                assert transaction["rewards_earned"] == expected_rewards
                break

    def test_no_rewards_for_non_purchases(self):
        """Test that non-purchase transactions don't earn rewards"""
        base_date = datetime.now()
        for i in range(100):
            transaction = generate_transaction(i, base_date)
            if transaction["transaction_type"] != "purchase":
                assert transaction["rewards_earned"] == 0

    def test_no_rewards_for_non_posted(self):
        """Test that non-posted transactions don't earn rewards"""
        base_date = datetime.now()
        for i in range(100):
            transaction = generate_transaction(i, base_date)
            if transaction["status"] != "posted":
                assert transaction["rewards_earned"] == 0

    def test_international_flag_consistency(self):
        """Test that international flag matches location country"""
        base_date = datetime.now()
        for i in range(50):
            transaction = generate_transaction(i, base_date)
            if transaction["is_international"]:
                # International transactions should have non-USA country
                assert transaction["location"]["country"] != "USA"
            # Note: Non-international can still be USA (but not always due to random logic)


class TestSeedDatabase:
    """Test suite for seed_database function"""

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_database_connection(self, mock_settings, mock_mongo_client):
        """Test that database connection is established correctly"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(10))
        mock_collection.aggregate.return_value = []

        seed_database(10)

        mock_mongo_client.assert_called_once_with("mongodb://localhost:27017")
        mock_client.__getitem__.assert_called_with("test_db")

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_clears_existing_data(self, mock_settings, mock_mongo_client):
        """Test that existing transactions are cleared"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(10))
        mock_collection.aggregate.return_value = []

        seed_database(10)

        mock_collection.delete_many.assert_called_once_with({})

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_inserts_correct_number_of_transactions(self, mock_settings, mock_mongo_client):
        """Test that correct number of transactions are inserted"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(50))
        mock_collection.aggregate.return_value = []

        seed_database(50)

        # Verify insert_many was called
        assert mock_collection.insert_many.called
        # Get the transactions that were passed to insert_many
        call_args = mock_collection.insert_many.call_args
        transactions = call_args[0][0]
        assert len(transactions) == 50

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_closes_connection(self, mock_settings, mock_mongo_client):
        """Test that database connection is closed"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(10))
        mock_collection.aggregate.return_value = []

        seed_database(10)

        mock_client.close.assert_called_once()

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    @patch('sys.exit')
    def test_handles_database_error(self, mock_exit, mock_settings, mock_mongo_client):
        """Test that database errors are handled gracefully"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_mongo_client.side_effect = Exception("Connection failed")

        seed_database(10)

        mock_exit.assert_called_once_with(1)

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_default_transaction_count(self, mock_settings, mock_mongo_client):
        """Test that default number of transactions is 500"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(500))
        mock_collection.aggregate.return_value = []

        seed_database()  # No argument, should use default

        call_args = mock_collection.insert_many.call_args
        transactions = call_args[0][0]
        assert len(transactions) == 500

    @patch('scripts.seed_credit_card_data.MongoClient')
    @patch('scripts.seed_credit_card_data.settings')
    def test_aggregation_statistics(self, mock_settings, mock_mongo_client):
        """Test that statistics aggregation is performed"""
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value.inserted_ids = list(range(10))
        mock_collection.aggregate.return_value = [
            {"_id": "groceries", "count": 5, "total": 250.50}
        ]

        seed_database(10)

        # Verify aggregate was called (at least once for statistics)
        assert mock_collection.aggregate.called
        assert mock_collection.aggregate.call_count >= 1


class TestDataConstants:
    """Test suite for data constants"""

    def test_merchants_categories_exist(self):
        """Test that merchant categories are defined"""
        expected_categories = [
            "groceries", "dining", "shopping", "travel",
            "entertainment", "utilities", "gas", "healthcare",
            "education", "other"
        ]
        for category in expected_categories:
            assert category in MERCHANTS

    def test_merchants_not_empty(self):
        """Test that each category has merchants"""
        for category, merchants in MERCHANTS.items():
            assert len(merchants) > 0
            assert all(isinstance(m, str) for m in merchants)

    def test_card_numbers_format(self):
        """Test that card numbers are masked correctly"""
        for card in CARD_NUMBERS:
            assert card.startswith("****")
            assert len(card) == 8
            assert card[4:].isdigit()

    def test_cardholders_count_matches_cards(self):
        """Test that number of cardholders matches number of cards"""
        assert len(CARDHOLDERS) == len(CARD_NUMBERS)

    def test_transaction_amounts_structure(self):
        """Test that transaction amounts are properly structured"""
        for category, (min_amt, max_amt) in TRANSACTION_AMOUNTS.items():
            assert isinstance(min_amt, (int, float))
            assert isinstance(max_amt, (int, float))
            assert min_amt < max_amt
            assert min_amt > 0

    def test_locations_structure(self):
        """Test that locations have required fields"""
        for location in LOCATIONS:
            assert "city" in location
            assert "state" in location
            assert "country" in location
            assert isinstance(location["city"], str)
            assert isinstance(location["state"], str)
            assert isinstance(location["country"], str)


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    def test_generate_transaction_with_recent_date(self):
        """Test transaction generation with recent base date"""
        base_date = datetime.now()
        transaction = generate_transaction(1, base_date)
        assert transaction is not None
        assert "transaction_id" in transaction

    def test_generate_transaction_with_past_date(self):
        """Test transaction generation with past base date"""
        base_date = datetime.now() - timedelta(days=365)
        transaction = generate_transaction(1, base_date)
        assert transaction is not None
        assert transaction["transaction_date"] <= base_date

    def test_generate_multiple_unique_transactions(self):
        """Test that multiple transactions have unique IDs"""
        base_date = datetime.now()
        transaction_ids = set()
        for i in range(100):
            transaction = generate_transaction(i, base_date)
            transaction_ids.add(transaction["transaction_id"])

        assert len(transaction_ids) == 100  # All unique

    def test_amount_precision(self):
        """Test that amounts are rounded to 2 decimal places"""
        base_date = datetime.now()
        for i in range(50):
            transaction = generate_transaction(i, base_date)
            amount_str = str(abs(transaction["amount"]))
            if "." in amount_str:
                decimal_places = len(amount_str.split(".")[1])
                assert decimal_places <= 2

    def test_rewards_precision(self):
        """Test that rewards are rounded to 2 decimal places"""
        base_date = datetime.now()
        for i in range(50):
            transaction = generate_transaction(i, base_date)
            rewards_str = str(transaction["rewards_earned"])
            if "." in rewards_str and transaction["rewards_earned"] > 0:
                decimal_places = len(rewards_str.split(".")[1])
                assert decimal_places <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
