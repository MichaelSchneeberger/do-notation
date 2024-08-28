from typing import Protocol

from donotation import do

from returns.context import RequiresContext

returns_do = do(attr='bind')

class _Deps(Protocol):  # we rely on abstractions, not direct values or types
    WORD_THRESHOLD: int
    UNGUESSED_CHAR: str

def _award_points_for_letters(guessed: int) -> RequiresContext[int, _Deps]:
    return RequiresContext(
        lambda deps: 0 if guessed < deps.WORD_THRESHOLD else guessed,
    )

@returns_do
def calculate_points(word: str):
    deps = yield RequiresContext[int, _Deps].ask()

    guessed_letters_count = len([
        letter for letter in word if letter != deps.UNGUESSED_CHAR
    ])
    return _award_points_for_letters(guessed_letters_count)

class Deps:
    WORD_THRESHOLD = 3
    UNGUESSED_CHAR = 'abc'

deps = Deps()
result = calculate_points(word='example')(deps)

# Output will be 7
print(result)
