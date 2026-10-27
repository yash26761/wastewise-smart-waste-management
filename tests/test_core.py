import os
import tempfile
import unittest
from pathlib import Path

class WasteWiseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        import database
        self.db = database
        self.old = database.DB_PATH
        database.DB_PATH = Path(self.tmp.name) / 'test.db'
        database.init_db()

    def tearDown(self):
        self.db.DB_PATH = self.old
        self.tmp.cleanup()

    def test_seed_and_summary(self):
        from analytics import frame, summary
        records = self.db.list_bins()
        self.assertEqual(len(records), 36)
        result = summary(frame(records))
        self.assertEqual(result['total'], 36)
        self.assertGreater(result['pending'], 0)

    def test_crud_and_priority(self):
        from analytics import frame
        self.db.add_bin('bin-101', 'Andheri', 'College Gate', 'Plastic', 95, 240)
        rec = next(r for r in self.db.list_bins() if r['bin_code'] == 'BIN-101')
        self.assertEqual(frame([rec]).iloc[0]['priority'], 'High')
        self.db.update_bin(rec['id'], 'Andheri', 'College Gate', 'Plastic', 75, 240)
        rec = next(r for r in self.db.list_bins() if r['id'] == rec['id'])
        self.assertEqual(frame([rec]).iloc[0]['priority'], 'Medium')
        self.db.report_overflow(rec['id'])
        rec = next(r for r in self.db.list_bins() if r['id'] == rec['id'])
        self.assertEqual(frame([rec]).iloc[0]['priority'], 'High')
        self.db.change_status(rec['id'], 'Collected')
        rec = next(r for r in self.db.list_bins() if r['id'] == rec['id'])
        self.assertEqual(frame([rec]).iloc[0]['priority'], 'Completed')
        self.db.delete_bin(rec['id'])
        self.assertEqual(len(self.db.list_bins()), 36)

    def test_duplicate_and_validation(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_bin('BIN-001', 'Andheri', 'Test', 'Dry', 50, 240)
        with self.assertRaises(ValueError):
            self.db.add_bin('BAD', 'Andheri', 'Test', 'Dry', 101, 240)
        with self.assertRaises(ValueError):
            self.db.change_status(1, 'Lost')

    def test_spark_analytics(self):
        from analytics import frame, spark_analytics
        records = self.db.list_bins()[:5]
        res = spark_analytics(frame(records))
        self.assertEqual(res['processed'], 5)
        self.assertIn('area', res)
        self.assertIn('type', res)
        self.assertIn('status', res)

if __name__ == '__main__':
    unittest.main()
