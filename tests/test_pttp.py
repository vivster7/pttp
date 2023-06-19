import unittest
import subprocess
import pathlib


class PttpTest(unittest.TestCase):
    def test_pttp(self):
        testdata_path = pathlib.Path(__file__).parent / 'testdata'
        example_program = testdata_path / 'example_program.py'
        old_data = testdata_path / 'old_example_program.speedscope.json'
        subprocess.run(['pttp', str(example_program)])

        new_data = testdata_path / 'example_program.speedscope.json'

        for a, b in zip(old_data.read_text().splitlines(), new_data.read_text().splitlines()):
            if ("at" in a and "at" in b) or ("startValue" in a and "startValue" in b):
                continue
            self.assertEqual(a, b)

        new_data.unlink()
