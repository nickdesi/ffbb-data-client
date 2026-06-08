import unittest
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from uuid import UUID

from ffbb_data_client.utils.converter_utils import (
    from_bool,
    from_datetime,
    from_duration,
    from_enum,
    from_float,
    from_int,
    from_list,
    from_obj,
    from_officiels_list,
    from_phone,
    from_str,
    from_time,
    from_timestamp,
    from_uuid,
)


class DummyEnum(Enum):
    VAL1 = "val1"
    VAL2 = "val2"


class TestConverterUtilsExtended(unittest.TestCase):
    def test_from_officiels_list(self):
        self.assertIsNone(from_officiels_list(None))
        self.assertEqual(from_officiels_list(["a", "b"]), ["a", "b"])
        self.assertEqual(from_officiels_list("a, b"), ["a", "b"])
        self.assertIsNone(from_officiels_list(""))
        self.assertIsNone(from_officiels_list(123))

    def test_from_str(self):
        obj = {"key": "value", "key_int": 123, "key_none": None}
        self.assertEqual(from_str(obj, "key"), "value")
        self.assertEqual(from_str(obj, "key_int"), "123")
        self.assertIsNone(from_str(obj, "key_none"))
        self.assertIsNone(from_str(obj, "missing"))

        # Test object that raises TypeError on str conversion (though unlikely in python)
        class BadStr:
            def __str__(self):
                raise TypeError("bad str")

        self.assertIsNone(from_str({"k": BadStr()}, "k"))

    def test_from_int(self):
        obj = {
            "int": 42,
            "str_int": "42",
            "str_empty": "   ",
            "str_bad": "abc",
            "float": 42.5,
            "bool": True,
            "none": None,
        }
        self.assertEqual(from_int(obj, "int"), 42)
        self.assertEqual(from_int(obj, "str_int"), 42)
        self.assertIsNone(from_int(obj, "str_empty"))
        self.assertIsNone(from_int(obj, "str_bad"))
        self.assertEqual(from_int(obj, "float"), 42)
        self.assertIsNone(from_int(obj, "bool"))  # bool is instance of int but excluded
        self.assertIsNone(from_int(obj, "none"))

    def test_from_float(self):
        obj = {
            "float": 42.5,
            "int": 42,
            "str_float": "42.5",
            "str_bad": "abc",
            "bool": True,
            "none": None,
        }
        self.assertEqual(from_float(obj, "float"), 42.5)
        self.assertEqual(from_float(obj, "int"), 42.0)
        self.assertEqual(from_float(obj, "str_float"), 42.5)
        self.assertIsNone(from_float(obj, "str_bad"))
        self.assertIsNone(from_float(obj, "bool"))
        self.assertIsNone(from_float(obj, "none"))

    def test_from_bool(self):
        obj = {
            "bool": True,
            "str_true": "true",
            "str_false": "false",
            "str_bad": "abc",
            "int": 1,
            "none": None,
        }
        self.assertTrue(from_bool(obj, "bool"))
        self.assertTrue(from_bool(obj, "str_true"))
        self.assertFalse(from_bool(obj, "str_false"))
        self.assertIsNone(from_bool(obj, "str_bad"))
        self.assertIsNone(from_bool(obj, "int"))
        self.assertIsNone(from_bool(obj, "none"))

    def test_from_datetime(self):
        obj = {
            "iso": "2026-05-24T12:00:00+00:00",
            "iso_z": "2026-05-24T12:00:00Z",
            "complex": "24 May 2026 12:00:00",
            "bad": "abc",
            "int": 123,
            "none": None,
        }
        self.assertEqual(
            from_datetime(obj, "iso"),
            datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            from_datetime(obj, "iso_z"),
            datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(from_datetime(obj, "complex"), datetime(2026, 5, 24, 12, 0))
        self.assertIsNone(from_datetime(obj, "bad"))
        self.assertIsNone(from_datetime(obj, "int"))
        self.assertIsNone(from_datetime(obj, "none"))

    def test_from_time(self):
        obj = {
            "hms": "12:30:45",
            "hm": "12:30",
            "bad_colon": "12:abc:45",
            "hhmm": "1230",
            "bad_hhmm": "9999",
            "bad_str": "abc",
            "time_obj": time(12, 30),
            "int": 123,
            "none": None,
        }
        self.assertEqual(from_time(obj, "hms"), time(12, 30, 45))
        self.assertEqual(from_time(obj, "hm"), time(12, 30, 0))
        self.assertIsNone(from_time(obj, "bad_colon"))
        self.assertEqual(from_time(obj, "hhmm"), time(12, 30))
        self.assertIsNone(from_time(obj, "bad_hhmm"))
        self.assertIsNone(from_time(obj, "bad_str"))
        self.assertEqual(from_time(obj, "time_obj"), time(12, 30))
        self.assertIsNone(from_time(obj, "int"))
        self.assertIsNone(from_time(obj, "none"))

    def test_from_enum(self):
        obj = {"enum": "val1", "bad": "val3", "none": None}
        self.assertEqual(from_enum(DummyEnum, obj, "enum"), DummyEnum.VAL1)
        self.assertIsNone(from_enum(DummyEnum, obj, "bad"))
        self.assertIsNone(from_enum(DummyEnum, obj, "none"))

    def test_from_obj(self):
        def fn(x):
            return x.get("val")

        obj = {"dict": {"val": 42}, "scalar": 123, "none": None}
        self.assertEqual(from_obj(fn, obj, "dict"), 42)
        self.assertIsNone(from_obj(fn, obj, "scalar"))
        self.assertIsNone(from_obj(fn, obj, "none"))

    def test_from_list(self):
        def fn(x):
            return x * 2

        obj = {"list": [1, 2, 3], "scalar": 123, "none": None}
        self.assertEqual(from_list(fn, obj, "list"), [2, 4, 6])
        self.assertIsNone(from_list(fn, obj, "scalar"))
        self.assertIsNone(from_list(fn, obj, "none"))

    def test_from_uuid(self):
        uuid_str = "12345678-1234-5678-1234-567812345678"
        obj = {
            "uuid": uuid_str,
            "bad": "abc",
            "int": 123,
            "none": None,
        }
        self.assertEqual(from_uuid(obj, "uuid"), UUID(uuid_str))
        self.assertIsNone(from_uuid(obj, "bad"))
        self.assertIsNone(from_uuid(obj, "int"))
        self.assertIsNone(from_uuid(obj, "none"))

    def test_from_duration(self):
        obj = {
            "delta": timedelta(hours=5),
            "num": 5.5,
            "str_empty": "   ",
            "str_h": "37h30",
            "str_h_only": "5h",
            "str_h_bad": "abc_h_def",
            "str_num": "5.5",
            "str_num_bad": "abc",
            "bad_type": {},
            "none": None,
        }
        self.assertEqual(from_duration(obj, "delta"), timedelta(hours=5))
        self.assertEqual(from_duration(obj, "num"), timedelta(hours=5, minutes=30))
        self.assertIsNone(from_duration(obj, "str_empty"))
        self.assertEqual(from_duration(obj, "str_h"), timedelta(hours=37, minutes=30))
        self.assertEqual(
            from_duration(obj, "str_h_only"), timedelta(hours=5, minutes=0)
        )
        self.assertIsNone(from_duration(obj, "str_h_bad"))
        self.assertEqual(from_duration(obj, "str_num"), timedelta(hours=5, minutes=30))
        self.assertIsNone(from_duration(obj, "str_num_bad"))
        self.assertIsNone(from_duration(obj, "bad_type"))
        self.assertIsNone(from_duration(obj, "none"))

    def test_from_timestamp(self):
        obj = {
            "num": 1782297600,
            "str_num": "1782297600",
            "str_empty": "   ",
            "str_bad": "abc",
            "bool": True,
            "bad_type": {},
            "none": None,
        }
        expected = datetime(2026, 6, 24, 10, 40, tzinfo=timezone.utc)
        self.assertEqual(from_timestamp(obj, "num"), expected)
        self.assertEqual(from_timestamp(obj, "str_num"), expected)
        self.assertIsNone(from_timestamp(obj, "str_empty"))
        self.assertIsNone(from_timestamp(obj, "str_bad"))
        self.assertIsNone(from_timestamp(obj, "bool"))
        self.assertIsNone(from_timestamp(obj, "bad_type"))
        self.assertIsNone(from_timestamp(obj, "none"))

    def test_from_phone(self):
        obj = {
            "str": "0606060606",
            "str_empty": "   ",
            "int": 606060606,
            "bool": True,
            "none": None,
        }
        self.assertEqual(from_phone(obj, "str"), "0606060606")
        self.assertIsNone(from_phone(obj, "str_empty"))
        self.assertEqual(from_phone(obj, "int"), "606060606")
        self.assertIsNone(from_phone(obj, "bool"))
        self.assertIsNone(from_phone(obj, "none"))
