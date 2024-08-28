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
        z = yield Writer(x + y, f'adding {x} and {y}')  # NameError: name 'y' is not defined
        return Writer(z, '')
    
    return inner_write()

# Output will be (3, adding 1 and 2)
print(stacked())
