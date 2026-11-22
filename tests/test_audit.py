import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from barcode_generation_claim_audit.audit import audit, evidence, paragraphs, pattern
from barcode_generation_claim_audit.phrases import BARCODEGENERATION, NOBARCODEGENERATION, GENERIC_NAMES


class AuditTests(unittest.TestCase):
    def test_phrase_lists(self):
        self.assertEqual((len(set(BARCODEGENERATION)), len(set(NOBARCODEGENERATION)), len(set(GENERIC_NAMES))), (50, 24, 24))
        yes, no = pattern(BARCODEGENERATION), pattern(NOBARCODEGENERATION)
        for phrase in NOBARCODEGENERATION:
            with self.subTest(phrase=phrase):
                self.assertIsNotNone(yes.search(phrase))
                self.assertIsNone(yes.search(no.sub(' ', phrase)))
        self.assertEqual(paragraphs('a\n```\ngenerate barcode\n```\nb'), ['a', 'b'])

    def test_routes(self):
        positive = ['import barcode as b\nb.get("x", "123")', 'from barcode import get_barcode as g\ng("x", code="1")', 'import barcode\nbarcode.generate()', 'from barcode import generate as g\ng()', 'import treepoem as t\nt.generate_barcode()', 'from treepoem import generate_barcode as g\ng()', 'from other import make_barcode as m\nm()', 'x = object()\nx.generate_code128()']
        positive += ['import barcode\nbarcode.' + cls + '()\nx.' + method + '()' for cls in 'Code39 Code128 Gs1_128 PZN PZN7 PZN8 EAN13 EAN13_GUARD EAN8 EAN8_GUARD EAN14 JAN UPCA ISBN13 ISBN10 ISSN ITF CODABAR'.split() for method in ('save', 'write', 'render', 'build')]
        positive += ['from pystrich.' + module + ' import ' + cls + ' as E\nE()\nx.' + method + '()' for module, cls in [('code128','Code128Encoder'),('code39','Code39Encoder'),('ean13','EAN13Encoder'),('itf','ITFEncoder'),('itf','ITF14Encoder')] for method in 'get_imagedata get_pilimage save get_svg save_svg get_eps save_eps png_dataurl svg_dataurl'.split()]
        positive += ['import pystrich as p\np.code128.Code128Encoder()\nx.save()']
        positive += ['x.' + name + '()' for name in GENERIC_NAMES]
        for source in positive:
            with self.subTest(source=source):
                self.assertTrue(evidence(source))

    def test_non_evidence(self):
        cases = ['import barcode', 'import barcode\nbarcode.get("x")', 'get("x", "1")', 'import barcode\nbarcode.get_class("x")', 'import barcode\nbarcode.get_barcode_class("x")', 'import barcode\nbarcode.Code128()', 'x.save()', 'import treepoem\ntreepoem.BarcodeType', 'import pystrich\npystrich.code128.Code128Encoder()', 'x.get_svg()', '"generate barcode"', 'x.generate_barcode', 'bad syntax !!!', 'import qrcode\nqrcode.make("x")', 'import segno\nsegno.make("x")', 'from pyzbar import decode\ndecode(x)', 'import zxingcpp\nzxingcpp.read_barcode(x)', 'Image.save(x)', 'import subprocess\nsubprocess.run("zint")', 'def generate_barcode(): pass\nx.generate_barcode()', 'import barcode\nbarcode = 1\nbarcode.generate()', 'import barcode\nwith thing() as barcode: barcode.generate()', 'from barcode import generate as g\ng = 1\ng()']
        cases += ['import pystrich\npystrich.' + cls + '()\nx.save()' for cls in ('AztecEncoder', 'DataMatrixEncoder', 'QRCodeEncoder', 'PDF417Encoder')]
        for source in cases:
            with self.subTest(source=source):
                self.assertFalse(evidence(source))

    def test_findings_and_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'README.md').write_text('We generate barcode.')
            self.assertEqual(audit(root)['findings'][0]['severity'], 'HIGH')
            (root/'tests').mkdir()
            (root/'tests/test_x.py').write_text('import barcode\nbarcode.generate()')
            self.assertEqual(audit(root)['findings'][0]['severity'], 'MEDIUM')
            self.assertEqual(audit(root, fail_on='medium')['verdict'], 'FAIL')
            (root/'source.py').write_text('import barcode\nbarcode.Code128()')
            (root/'other.py').write_text('x.save()')
            self.assertEqual(audit(root)['findings'][0]['severity'], 'MEDIUM')
            (root/'source.py').write_text('import barcode\nbarcode.Code128()\nx.save()')
            self.assertEqual(audit(root)['verdict'], 'PASS')
            (root/'README.md').write_text('It does not generate barcode.')
            self.assertEqual(audit(root)['findings'][0]['rule'], 'documented-no-barcode-generation-claim-false')
            self.assertEqual(audit(root, ignore=['source.py'])['verdict'], 'PASS')

    def test_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, 'README.md').write_text('generate barcode')
            result = subprocess.run([sys.executable, '-m', 'barcode_generation_claim_audit', 'audit', temp, '--json'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['findings'][0]['severity'], 'HIGH')
            self.assertEqual(subprocess.run([sys.executable, '-m', 'barcode_generation_claim_audit', 'audit', '--fail-on', 'bad'], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run([sys.executable, '-m', 'barcode_generation_claim_audit', '--version'], capture_output=True, text=True).stdout.strip(), '0.1.0')

    def test_self_audit(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(audit(root)['verdict'], 'PASS')
        self.assertFalse(any(pattern(BARCODEGENERATION).search(p) or pattern(NOBARCODEGENERATION).search(p) for p in paragraphs((root/'README.md').read_text())))


if __name__ == '__main__':
    unittest.main()
