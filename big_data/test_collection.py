import json, tempfile, unittest
from pathlib import Path
from big_data.collect_official import normalize_municipalities, save_snapshot

class CollectionTests(unittest.TestCase):
    def test_normalize_territory_without_personal_fields(self):
        result=normalize_municipalities([{'id':3500105,'nome':'Adamantina','microrregiao':{'mesorregiao':{'UF':{'id':35,'sigla':'SP','nome':'Sao Paulo'}}}}])
        self.assertEqual(result,[{'municipality_id':3500105,'municipality':'Adamantina','state_id':35,'state_code':'SP','state':'Sao Paulo'}])
    def test_reject_invalid_or_duplicate_territory(self):
        with self.assertRaises(ValueError): normalize_municipalities([{'id':1,'nome':''}])
        row={'id':3500105,'nome':'A','microrregiao':{'mesorregiao':{'UF':{'id':35,'sigla':'SP','nome':'Sao Paulo'}}}}
        with self.assertRaises(ValueError): normalize_municipalities([row,row])
    def test_snapshot_manifest_and_content_addressing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); spec={'id':'test','url':'https://example.com/public','extension':'json','license_status':'test'}
            a=save_snapshot(p,spec,b'[]',{'status':200})
            b=save_snapshot(p,spec,b'[]',{'status':200})
            self.assertEqual(a['sha256'],b['sha256'])
            self.assertEqual(a['raw_path'],b['raw_path'])
            self.assertEqual(len(list((p/'manifests').glob('*.json'))),2)
            self.assertFalse(a['synthetic'])
