from __future__ import annotations
from typing import Callable, Generator
from donotation import do

class StateMonad[S, T]:
    def __init__(self, func: Callable[[S], tuple[S, T]]):
        self.func = func

    # Specifies the return type of the `yield from` operator
    def __iter__(self) -> Generator[None, None, T]: ...

    def flat_map[U](self, func: Callable[[T], StateMonad[S, U]]):
        def next(state):
            n_state, value = self.func(state)
            return func(value).func(n_state)

        return StateMonad(func=next)

def collect_even_numbers(num: int):
    def func(state: set[int]):
        if num % 2 == 0:
            state = state | {num}

        return state, num
    return StateMonad(func)

@do()
def example(init):
    x = yield from collect_even_numbers(init+1)
    y = yield from collect_even_numbers(x+1)
    z = yield from collect_even_numbers(y+1)
    return collect_even_numbers(z+1)

# Correct type hint is inferred
monad = example(3)

state = set[int]()
state, value = monad.func(state)

# Output will be valuqe=7
print(f'{value=}')
# Output will be state={4, 6}
print(f'{state=}')
