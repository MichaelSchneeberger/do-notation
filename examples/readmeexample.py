from donotation import do

class StateMonad:
    def __init__(self, func):
        self.func = func

    def flat_map(self, func):
        def next(state):
            n_state, value = self.func(state)
            return func(value).func(n_state)

        return StateMonad(func=next)

def collect_even_numbers(num: int):
    def func(state: set):
        if num % 2 == 0:
            state = state | {num}

        return state, num
    return StateMonad(func)

@do()
def example(init):
    x = yield collect_even_numbers(init+1)
    y = yield collect_even_numbers(x+1)
    z = yield collect_even_numbers(y+1)
    return collect_even_numbers(z+1)

state = set[int]()
state, value = example(3).func(state)

# Output will be value=7
print(f'{value=}')
# Output will be state={4, 6}
print(f'{state=}')