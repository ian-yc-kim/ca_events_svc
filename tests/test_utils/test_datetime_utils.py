"""Tests for datetime utility functions."""

import pytest
from datetime import datetime, timezone, timedelta
from app.utils.datetime import ensure_utc_aware


class TestEnsureUtcAware:
    """Test cases for ensure_utc_aware function."""
    
    def test_valid_utc_datetime_string_z_suffix(self):
        """Test valid UTC datetime string with 'Z' suffix."""
        input_str = "2025-01-15T10:30:00Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_valid_utc_datetime_string_offset(self):
        """Test valid UTC datetime string with +00:00 offset."""
        input_str = "2025-01-15T10:30:00+00:00"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_valid_positive_offset_conversion(self):
        """Test datetime with positive offset converts to UTC correctly."""
        input_str = "2025-01-15T15:30:00+05:00"
        result = ensure_utc_aware(input_str)
        
        # 15:30 +05:00 should become 10:30 UTC
        expected = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_valid_negative_offset_conversion(self):
        """Test datetime with negative offset converts to UTC correctly."""
        input_str = "2025-01-15T05:30:00-05:00"
        result = ensure_utc_aware(input_str)
        
        # 05:30 -05:00 should become 10:30 UTC
        expected = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_valid_datetime_object_utc(self):
        """Test valid UTC datetime object passes through."""
        input_dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = ensure_utc_aware(input_dt)
        
        assert result == input_dt
        assert result.tzinfo == timezone.utc
    
    def test_valid_datetime_object_with_offset_conversion(self):
        """Test datetime object with offset converts to UTC."""
        offset_tz = timezone(timedelta(hours=5))
        input_dt = datetime(2025, 1, 15, 15, 30, 0, tzinfo=offset_tz)
        result = ensure_utc_aware(input_dt)
        
        # 15:30 +05:00 should become 10:30 UTC
        expected = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_iso_8601_with_microseconds(self):
        """Test ISO 8601 format with microseconds."""
        input_str = "2025-01-15T10:30:00.123456Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 1, 15, 10, 30, 0, 123456, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_iso_8601_with_partial_microseconds(self):
        """Test ISO 8601 format with partial microseconds."""
        input_str = "2025-01-15T10:30:00.123Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 1, 15, 10, 30, 0, 123000, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_timezone_naive_datetime_object_rejected(self):
        """Test that timezone-naive datetime object is rejected."""
        naive_dt = datetime(2025, 1, 15, 10, 30, 0)  # No timezone
        
        with pytest.raises(ValueError, match="Timezone-naive datetime not allowed"):
            ensure_utc_aware(naive_dt)
    
    def test_timezone_naive_string_rejected(self):
        """Test that timezone-naive datetime string is rejected."""
        naive_str = "2025-01-15T10:30:00"  # No timezone info
        
        with pytest.raises(ValueError, match="Timezone-naive datetime not allowed"):
            ensure_utc_aware(naive_str)
    
    def test_invalid_datetime_format_rejected(self):
        """Test that invalid datetime format is rejected."""
        invalid_str = "invalid-datetime-format"
        
        with pytest.raises(ValueError, match="Invalid datetime format"):
            ensure_utc_aware(invalid_str)
    
    def test_none_value_rejected(self):
        """Test that None value is rejected."""
        with pytest.raises(ValueError, match="Datetime value cannot be None"):
            ensure_utc_aware(None)
    
    def test_empty_string_rejected(self):
        """Test that empty string is rejected."""
        with pytest.raises(ValueError, match="Datetime string cannot be empty"):
            ensure_utc_aware("")
    
    def test_whitespace_string_rejected(self):
        """Test that whitespace-only string is rejected."""
        with pytest.raises(ValueError, match="Datetime string cannot be empty"):
            ensure_utc_aware("   ")
    
    def test_unsupported_type_rejected(self):
        """Test that unsupported input types are rejected."""
        with pytest.raises(ValueError, match="Unsupported datetime type"):
            ensure_utc_aware(12345)  # integer
        
        with pytest.raises(ValueError, match="Unsupported datetime type"):
            ensure_utc_aware(["2025-01-15T10:30:00Z"])  # list
    
    def test_edge_case_leap_second(self):
        """Test handling of leap second (59 seconds is valid)."""
        # Note: Python datetime doesn't support leap seconds (60 seconds)
        # but 59 seconds should work fine
        input_str = "2025-06-30T23:59:59Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_edge_case_february_29_leap_year(self):
        """Test handling of February 29 in leap year."""
        input_str = "2024-02-29T10:30:00Z"  # 2024 is a leap year
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2024, 2, 29, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc
    
    def test_edge_case_year_boundaries(self):
        """Test handling of year boundaries."""
        # New Year's Eve
        input_str = "2024-12-31T23:59:59Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert result == expected
        
        # New Year's Day
        input_str = "2025-01-01T00:00:00Z"
        result = ensure_utc_aware(input_str)
        
        expected = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected
    
    def test_various_timezone_offsets(self):
        """Test various timezone offsets are converted correctly."""
        test_cases = [
            ("2025-01-15T10:30:00+01:00", datetime(2025, 1, 15, 9, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T10:30:00+12:00", datetime(2025, 1, 14, 22, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T10:30:00-11:00", datetime(2025, 1, 15, 21, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T10:30:00+05:30", datetime(2025, 1, 15, 5, 0, 0, tzinfo=timezone.utc)),  # India Standard Time
            ("2025-01-15T10:30:00-08:00", datetime(2025, 1, 15, 18, 30, 0, tzinfo=timezone.utc)),  # PST
        ]
        
        for input_str, expected in test_cases:
            result = ensure_utc_aware(input_str)
            assert result == expected, f"Failed for input: {input_str}"
            assert result.tzinfo == timezone.utc
    
    def test_z_suffix_variations(self):
        """Test various 'Z' suffix scenarios."""
        test_cases = [
            "2025-01-15T10:30:00Z",
            "2025-01-15T10:30:00.123Z",
            "2025-01-15T10:30:00.123456Z",
        ]
        
        for input_str in test_cases:
            result = ensure_utc_aware(input_str)
            assert result.tzinfo == timezone.utc
            # Verify it's equivalent to the +00:00 version
            equivalent_str = input_str[:-1] + "+00:00"
            equivalent_result = ensure_utc_aware(equivalent_str)
            assert result == equivalent_result
