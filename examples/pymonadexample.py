from donotation import do

from pymonad.maybe import Just
from pymonad.writer import Writer

pymonad_do = do(attr='bind')

@pymonad_do
def stacked():
    x = yield Just(1)
    y = yield Just(2)

    @pymonad_do
    def inner_write():
        yield Writer(x + y, f'adding {x} and {y}')

    return inner_write()

# Output will be 3
print(stacked())
