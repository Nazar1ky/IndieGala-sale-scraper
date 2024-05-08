import unittest

from main import parse_page
from tests.data import data1


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self) -> None:  # noqa: ANN102
        with open("tests/page1.html", encoding="utf-8") as file:
            self.test_data = file.read()

    def test_parse_page(self) -> None:  # noqa: ANN101
        result = parse_page(self.test_data)

        self.assertEqual(result[0], data1[0])
        self.assertCountEqual(result[1], data1[1])

        for test_product, product in zip(result[1], data1[1], strict=False):
            self.assertEqual(test_product, product)

if __name__ == "__main__":
    unittest.main()
