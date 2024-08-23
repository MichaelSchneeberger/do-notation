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
def example():
    x = yield collect_even_numbers(init + 1)
    """
    Traceback (most recent call last):
    File "[...]\donotation\main.py", line 9, in <module>
        import examples.localvariablesexample
    File "[...]\donotation\examples\localvariablesexample.py", line 36, in <module>
        state, value = example().func(state)
                    ^^^^^^^^^
    File "[...]\donotation\examples\localvariablesexample.py", line 27, in example
        x = yield collect_even_numbers(init + 1)
                                    ^^^^
    NameError: name 'init' is not defined. Did you mean: 'int'?
    """
    y = yield collect_even_numbers(x + 1)
    z = yield collect_even_numbers(y + 1)
    return collect_even_numbers(z + 1)


# local variable is defined after do decorator function is called
init = 3

state = set[int]()

state, value = example().func(state)
