def complex_thang(*args): pass

x = 1
y = 2

def test_complex_thang(q=1,w=2):
    assert complex_thang(1) == 1
    assert complex_thang(6) == 1

def test_complex_thang(q=1, w=2):
    assert complex_thang(5) == 1
    assert complex_thang(2) is None


def test_2():
    global x
    if x:
        assert 1 == 1
    elif x == 2:
        assert 6 == 1
    else:
        assert 5 == 1
    assert 2 is None


def test_3():
    global y
    if y:
        assert 1 == 2
    elif y == 2:
        assert 6 == 5
    else:
        assert 5 == 5
    assert 2 is None


test_2()
test_3()

v = 0
