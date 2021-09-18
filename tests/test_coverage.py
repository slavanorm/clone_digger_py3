from main import main
import os

os.chdir('..')

def test_1():
    #main('tests/test_me.py')
    # todo: why does it report a list?
    main('../wealth-pct-main-api/run_flask.py')

test_1()
