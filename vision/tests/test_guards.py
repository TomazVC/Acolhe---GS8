import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from vision import service, train

class GuardTests(unittest.TestCase):
    def test_class_order_and_ids(self):
        names = list(service.LABELS)
        self.assertEqual(train.validate_names(names), names)
        self.assertEqual(train.validate_names(dict(enumerate(names))), names)
        for invalid in [names[::-1], names[:-1], names + [names[0]], {str(i): n for i,n in enumerate(names)}, {i+1:n for i,n in enumerate(names)}, None]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                train.validate_names(invalid)

    def test_yaml_and_provenance_checked_before_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)/'data.yaml'; data.write_text('names: []')
            provenance=Path(tmp)/'provenance.json'
            provenance.write_text(json.dumps(dict(source_url='https://example.org',license='CC BY',split_method='separate',real_images=True,class_names=list(service.LABELS))))
            try:
                import yaml
            except ImportError:
                self.skipTest("PyYAML optional training dependency not installed")
            for names in [list(service.LABELS)[::-1], list(service.LABELS)[:-1]]:
                data.write_text(yaml.safe_dump({'names':names,'train':'train','val':'val','test':'test'}))
                with self.assertRaises(ValueError): train.validate_dataset(data,provenance)
            data.write_text(yaml.safe_dump({'names':list(service.LABELS),'train':'train','val':'val','test':'test'}))
            self.assertEqual(train.validate_dataset(data,provenance)[1]['class_names'],list(service.LABELS))
            data.write_text(data.read_text() + '\nnames: []\n')
            with self.assertRaises(ValueError): train.validate_dataset(data,provenance)

    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'artifacts'; out.mkdir(); (out/'best.pt').write_bytes(b'original')
            with self.assertRaises(FileExistsError): train.reserve_output(out)
            self.assertEqual((out/'best.pt').read_bytes(),b'original')

    def test_invalid_manifest_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/'best.pt'; model.write_bytes(b'checkpoint')
            manifest=Path(tmp)/'model_manifest.json'
            with patch.object(service,'MODEL',model), patch.object(service,'MANIFEST',manifest):
                for content in ['{','[]','{}',json.dumps({'trained_on_real_images':True,'class_names':list(service.LABELS),'checkpoint_sha256':'wrong'})]:
                    manifest.write_text(content)
                    self.assertFalse(service.status()['ready'])

    def test_valid_artifact_but_missing_runtime_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/'best.pt'; model.write_bytes(b'checkpoint')
            manifest=Path(tmp)/'model_manifest.json'
            manifest.write_text(json.dumps({'trained_on_real_images':True,'class_names':list(service.LABELS),'checkpoint_sha256':hashlib.sha256(b'checkpoint').hexdigest()}))
            with patch.object(service,'MODEL',model),patch.object(service,'MANIFEST',manifest),patch.dict('sys.modules',{'ultralytics':None}):
                self.assertFalse(service.status()['ready'])

    def test_load_and_model_classes_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/'best.pt'; model.write_bytes(b'checkpoint')
            manifest=Path(tmp)/'model_manifest.json'
            manifest.write_text(json.dumps({'trained_on_real_images':True,'class_names':list(service.LABELS),'checkpoint_sha256':hashlib.sha256(b'checkpoint').hexdigest()}))
            runtime=Mock(); runtime.YOLO.return_value.names=dict(enumerate(service.LABELS))
            with patch.object(service,'MODEL',model),patch.object(service,'MANIFEST',manifest),patch.dict('sys.modules',{'ultralytics':runtime,'PIL':Mock()}):
                self.assertTrue(service.status()['ready'])
                self.assertFalse(service.status()['quality_validated'])
                runtime.YOLO.return_value.names={0:'wrong'}
                self.assertFalse(service.status()['ready'])
                runtime.YOLO.side_effect=RuntimeError('invalid checkpoint')
                self.assertFalse(service.status()['ready'])

    def test_fresh_output_reserved_exclusively(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'new'
            self.assertEqual(train.reserve_output(out),out)
            with self.assertRaises(FileExistsError): train.reserve_output(out)
