from __future__ import annotations
from typing import Callable, Generator, Iterator
from donotation import do

class StateMonad[S, T]:
    def __init__(self, func: Callable[[S], tuple[S, T]]):
        self.func = func

    def __iter__(self) -> Generator[None, None, T]: ...
    # def __iter__(self) -> Iterator[T]: ...

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
    y = yield from collect_even_numbers(init*x+1)
    z = yield from collect_even_numbers(x*y+1)
    return collect_even_numbers(y*z+1)

state = set[int]()
state, value = example(3).func(state)

# Output will be {4, 690}
print(state)
