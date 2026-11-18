import unittest
from navigation import walking_path

class NavigationTests(unittest.TestCase):
    def test_detours_around_furniture(self):
        def clear(x,y):
            return 0<=x<=4 and 0<=y<=4 and not (1<=x<=3 and 1<=y<=3)
        path=walking_path((0,2),(4,2),clear)
        self.assertTrue(path)
        self.assertTrue(all(clear(*point) for point in path))
        self.assertEqual(path[0],(0,2))
        self.assertEqual(path[-1],(4,2))
        self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1])==.5 for a,b in zip(path,path[1:])))

    def test_unreachable(self):
        self.assertEqual(walking_path((0,0),(2,0),lambda x,y: x==0 and y==0),[])
