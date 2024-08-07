from donotation import do
from pymonad.writer import Writer

pymonad_do = do(attr='bind')

@pymonad_do
def write_1_2():
    x = yield Writer(1, '-got 1-')
    y = yield Writer(2, '-got 2-')
    yield Writer(x + y, f'-adding {x} and {y}-')

# Output will be (3, -got 1--got 2--adding 1 and 2-)
print(write_1_2())
