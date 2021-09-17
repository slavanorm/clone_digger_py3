from main import main
import os

os.chdir('..')

def test_1():
    main('tests/test_me.py')

test_1()

'''
#previous tests
class Elem:
    def __init__(self, code):
        self._code = code

    def getCode(self):
        return self._code

    def __str__(self):
        return str(self._code)

def test1():
    t = SuffixTree()
    for w in ["abcPeter", "Pet1erbca", "Peter", "aPet0--"]:
        t.add([Elem(c) for c in w])
    maxs = t.getBestMaxSubstrings(3)
    l = []
    for (s1, s2) in maxs:
        l.append(
            [
                "".join([str(e) for e in s1]),
                "".join([str(e) for e in s2]),
            ]
        )
    assert l == [
        ["Pe1t", "P2et"],
        ["P3et", "Pe4t"],
        ["Pet", "Pet"],
        ["Pet", "Pet"],
        ["Pet", "Pet"],
        ["Peter", "Peter"],
    ]

def test2():
    t = SuffixTree()
    for w in ["a", "aa"]:
        t.add([Elem(c) for c in w])
    maxs = t.getBestMaxSubstrings(0)
    l = []
    for (s1, s2) in maxs:
        l.append(
            [
                "".join([str(e) for e in s1]),
                "".join([str(e) for e in s2]),
            ]
        )
    assert l == [["a", "a"], ["a", "a"], ["a", "a"]]

for s in dir():
    if s.find("test") == 0:
        eval(s + "()")
'''