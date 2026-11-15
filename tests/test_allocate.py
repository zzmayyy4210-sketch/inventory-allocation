import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from allocate import allocate, allocate_partial, related_links, check


class AllocationTests(unittest.TestCase):
    def test_shared_inventory(self):
        stock = {'A': 10, 'B': 20}
        recipes = {'01': {'A': 1}, '02': {'B': 1}, '03': {'A': 1, 'B': 1}}
        self.assertEqual(allocate(stock, recipes)['plan'], {'01': 5, '02': 15, '03': 5})
        self.assertEqual(check(stock, recipes, {'01': 6, '02': 15, '03': 5})['items']['A']['shortage'], 1)

    def test_partial_dependencies(self):
        stock = {'A': 10, 'B': 20, 'C': 100}
        recipes = {'target': {'A': 1, 'B': 1}, 'A': {'A': 1},
                   'BC': {'B': 1, 'C': 1}, 'C': {'C': 1}}
        self.assertEqual(related_links(recipes, ['target']), ['A', 'BC'])
        self.assertEqual(allocate_partial(stock, recipes, ['target'], {'A': 4, 'BC': 8})['plan'], {'target': 6})
        with self.assertRaises(ValueError):
            allocate_partial(stock, recipes, ['target'], {'A': 4})
        with self.assertRaises(ValueError):
            allocate_partial(stock, recipes, ['target'], {'A': 11, 'BC': 8})

    def test_random_against_round_by_round(self):
        rng = random.Random(42)
        for _ in range(300):
            stock = {str(i): rng.randrange(15) for i in range(3)}
            recipes = {str(j): {str(i): rng.randrange(1, 4)
                       for i in rng.sample(range(3), rng.randrange(1, 4))} for j in range(4)}
            remaining, expected = dict(stock), dict.fromkeys(recipes, 0)
            while True:
                changed = False
                for link in sorted(recipes):
                    if all(remaining[s] >= n for s, n in recipes[link].items()):
                        changed = True
                        expected[link] += 1
                        for s, n in recipes[link].items():
                            remaining[s] -= n
                if not changed:
                    break
            result = allocate(stock, recipes)
            self.assertEqual(result['plan'], expected)
            self.assertTrue(result['audit']['passed'])


if __name__ == '__main__':
    unittest.main()
