import unittest
from unittest.mock import Mock, patch


class TestMaricopaAssessorConnector(unittest.TestCase):
    @patch("maricopa_assessor_connector.requests.get")
    def test_get_property_by_address_returns_property_on_success(
        self, mock_get: Mock
    ) -> None:
        # Arrange: mock HTTP response
        def side_effect(url: str, *args: object, **kwargs: object) -> Mock:
            resp = Mock()
            resp.raise_for_status.return_value = None
            if "/search/property/" in url:
                resp.status_code = 200
                resp.json.return_value = {
                    "results": [{"APN": "123-45-678"}],
                }
                return resp
            if "/parcel/123-45-678/residential-details" in url:
                resp.status_code = 200
                resp.json.return_value = {
                    "YearBuilt": 1999,
                    "SqFt": 1837,
                    "LotSizeSqFt": 7200,
                }
                return resp
            if "/parcel/123-45-678/valuations" in url:
                resp.status_code = 200
                resp.json.return_value = [{"TotalAssessedValue": 312000}]
                return resp

            # Default for other parcel endpoints we call
            resp.status_code = 200
            resp.json.return_value = {}
            return resp

        mock_get.side_effect = side_effect

        from maricopa_assessor_connector import MaricopaAssessorConnector

        conn = MaricopaAssessorConnector()
        # Force "connected" for unit test (connect() depends on env config)
        conn.connected = True

        # Act
        prop = conn.get_property_by_address(
            "3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296"
        )

        # Assert
        self.assertIsNotNone(prop)
        assert prop is not None
        self.assertEqual(prop.mls_number, "123-45-678")
        self.assertEqual(prop.year_built, 1999)
        self.assertEqual(prop.lot_size_sqft, 7200.0)
        self.assertEqual(prop.square_feet, 1837)
        self.assertEqual(prop.mls_data.get("source"), "maricopa_assessor")

    @patch("maricopa_assessor_connector.requests.get")
    def test_get_property_by_address_handles_auth_failure(self, mock_get: Mock) -> None:
        resp = Mock()
        resp.status_code = 401
        mock_get.return_value = resp

        from maricopa_assessor_connector import MaricopaAssessorConnector

        conn = MaricopaAssessorConnector()
        conn.connected = True

        prop = conn.get_property_by_address("a", "b", "AZ", "c")
        self.assertIsNone(prop)
        self.assertIn("auth_failed", conn.last_error or "")

    def test_get_property_by_address_non_az_returns_none(self) -> None:
        from maricopa_assessor_connector import MaricopaAssessorConnector

        conn = MaricopaAssessorConnector()
        conn.connected = True
        prop = conn.get_property_by_address("a", "b", "CA", "c")
        self.assertIsNone(prop)


if __name__ == "__main__":
    unittest.main()
