# Do-notation

Do-notation is a Python package that introduces Haskell-like do-notation using a Python decorator.

## Features

* Haskell-like Behavior: Emulate Haskell's do-notation for Python objects that implement the `flat_map` (or `bind`) method.
* Syntactic sugar: Use the `do` decorator to convert generator functions into nested `flat_map` method calls by using the Abstract Syntax Tree (AST).
* Simplified Syntax: Write complex nested `flat_map` sequences in a clean and readable way without needing to define auxillary functions.
* Minimalistic Implementation: The decorator relies on simple and straightforward conversion rules, reducing potential bugs and making it adaptable to a wide range of scenarios.
* Type hinting: The type hint of the value returned by the decorated generator function is correctly inferred by type checkers when using `yield from`.

## Installation

You can install Do-notation using pip:

```
pip install donotation
```

## Usage

### Basic Example

First, import the `do` decorator from the do-notation package. Then, define a class implementing the `flat_map` method to represent the monadic operations. Finally, use the `do` decorator on the generator function that yields objects of this class.

``` python
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
    x = yield collect_even_numbers(init + 1)
    y = yield collect_even_numbers(x + 1)
    z = yield collect_even_numbers(y + 1)

    # The generator function must return a `StateMonad` rather than the 
    # containerized value itself (unlike in other do-notation implementations).
    return collect_even_numbers(z + 1)

state = set[int]()
state, value = example(3).func(state)

print(f'{value=}')              # Output will be value=7
print(f'{state=}')              # Output will be state={4, 6}
```

In this example, we define a `StateMonad` class that implements a `flat_map` method to represent a state monad.
The helper method `collect_even_numbers` is used to generate a sequence of monadic operations within the generator function `example`, which stores the immediate values if they are even integer.
The `do` decorator converts the generator function `example` into a sequence of `flat_map` calls on the `StateMonad` objects. 

Unlike other do-notation implementations, the generator function must return an object that implements the `flat_map` method, rather than directly returning the containerized value. This design choice simplifies the library by only requiring the implementation of the `flat_map` method, avoiding the need for additional methods like `return` or `map`. Additionally, this approach ensures accurate type hint inference, making the code both cleaner and more type-safe.

### How It Works

The `do` decorator works by substituting the `yield` and `yield from` statements with nested `flat_map` calls using the Abstract Syntax Tree (AST) of the generator function. Here’s a breakdown of the process:

1. AST traversal: Traverse the AST of the generator function to inspect all statements.
2. Yield operation: When an yield operations is encountered, define an nested function containing the remaining statements. This nested function is then called within the `flat_map` method call.
3. If-else statements: If an if-else statement is encountered, traverse its AST to inspect all statements. If an yield statement is found, the nested function for the `flat_map` method includes the rest of the if-else statement and the remaining statements of the generator function.

The above example is conceptually translated into the following nested `flat_map` calls:

``` python
def example_translated(init):
    return collect_even_numbers(init + 1).flat_map(lambda x: 
        collect_even_numbers(x + 1).flat_map(lambda y: 
            collect_even_numbers(y + 1).flat_map(lambda z: 
                collect_even_numbers(z + 1)
            )
        )
    )
```

## Yield Placement Restrictions

The yield operations within the generator can only be placed within if-else statements but not within for or while statements. Yield statements within the for or while statement are not substituted by a monadic `flat_map` chaining, resulting in a generator function due to the leftover yield statements. In this case, an exception is raised.

### Good Example

Here’s a good example where the yield statement is only placed within if-else statements:

``` python
@do()
def good_example(init):
    if condition:
        x = yield collect_even_numbers(init)
    else:
        x = yield collect_even_numbers(init + 1)
    y = yield collect_even_numbers(x + 1)
    return collect_even_numbers(y + 1)

result = good_example(3)
```

### Bad Example

Here’s a bad example where the yield statement is placed within a for or while statement:

``` python
@do()
def bad_example(init):
    x = init
    for _ in range(3):
        x = yield collect_even_numbers(x)
    return collect_even_numbers(x + 1)

# This will raise an exception due to improper yield placement
result = bad_example(3)
```

## Customization

The `do` decorator can be customized to work with different implementations of the flat map operation.
There are two ways to change the bheavior of the `do` decorator:

### Custom Mehtod Name:

If the method is called "bind" instead of "flat_map", you can specify the method name when creating the decorator instance:

``` python
my_do = do(attr='bind')

@my_do()  # converts the generator function to nested `bind` method calls
def example():
    # ...
```

### External Flat Map Function:

If the flat map operation is defined as an external function rather than a method of the class, you can define a callback function:

``` python
flat_map = ...  # some implementation of the flat map operation

def callback(source, fn):
    return flat_map(source, fn)

my_do = do(callback=callback)

@my_do()  # calls the callback to perform a flat map operation
def example():
    # ...
```

In both cases, the `do` decorator adapts to the specified method name or external function, allowing for flexible integration with different monadic structures.


<!-- ## Decorator Implementation

Here is the pseudo-code of the `do` decorator:

``` python
def do(fn):
    def wrapper(*args, **kwargs):
        gen = fn(*args, **kwargs)

        def send_and_yield(value):
            try:
                next_val = gen.send(value)
            except StopIteration as e:
                result = e.value
            else:
                result = next_val.flat_map(send_and_yield)
            return result

        return send_and_yield(None)
    return wrapper
```

The provided code is a pseudo-code implementation that illustrates the core concept of the `do` decorator. 
The main difference between this pseudo-code and the actual implementation is that the function given to the `flat_map` method (i.e. `send_and_yield`) can only be called once in the pseudo-code, whereas in the real implementation, that function can be called arbitrarily many times.
This distinction is crucial for handling monadic operations correctly and ensuring that the `do` decorator works as expected in various scenarios. -->


<!-- ### Translating a Generator Function to nested `flat_map` Calls

To better understand how the `do` decorator translates a generator function into a nested sequence of `flat_map` calls, let's consider the following example function:

``` python
@do()
def example():
    x = yield Monad(1)
    y = yield Monad(x + 1)
    z = yield Monad(y + 1)
    return Monad(z + 1)
```

The above function is conceptually translated into the following nested `flat_map` calls:

``` python
def example_translated():
    return Monad(1).flat_map(lambda x: 
        Monad(x + 1).flat_map(lambda y: 
            Monad(y + 1).flat_map(lambda z: 
                Monad(z + 1)
            )
        )
    )
```

This translation shows how each yield in the generator function corresponds to a `flat_map` call that takes a lambda function, chaining the monadic operations together. -->

## Type hints

When using the `yield` operator, type checkers cannot infer the correct types for the values returned by it. In the basic example above, a type checker like Pyright may infer `Unknown` for the variables `x`, `y`, and `z`, even though they should be of type `int`.

To address this issue, you can use the `yield from` operator instead of `yield`. The `yield from` operator can be better supported by type checkers, ensuring that the correct types are inferred. To make this work properly, you need to annotate the return type of the `__iter__` method in the monadic class (e.g., `StateMonad`).

Here’s how to set it up:

``` python
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

@do()
def example(init):
    x: int = yield from collect_even_numbers(init+1)
    y: int = yield from collect_even_numbers(x+1)
    z: int = yield from collect_even_numbers(y+1)
    return collect_even_numbers(z+1)

# Correct type hint is inferred
m: StateMonad[int] = example(3)
```

## Limitations

<!-- ### Yield placement restriction

As described above, the yield statement cannot be placed inside a `for` or `while` loop. -->

### Local variables

Local variables defined after the point where the `do` decorator is applied to the genertor function cannot be accessed within the generator function.
The following example raises a `NamedError` exception.

``` python
x = 1

@do()
def apply_write():
    # NameError: name 'y' is not defined
    return Writer(x + y, f'adding {x} and {y}')

y = 2
```


## References

Here are some other Python libraries that implement the do-notation:

* [https://github.com/jasondelaat/pymonad](https://github.com/jasondelaat/pymonad)
* [https://github.com/dry-python/returns](https://github.com/dry-python/returns)
* [https://github.com/TRCYX/py_monad_do](https://github.com/TRCYX/py_monad_do)
* [https://github.com/dbrattli/Expression](https://github.com/dbrattli/Expression)

These libaries implement the `do` decorator as a real generator, similar to the following pseudo-code:

``` python
def do(fn):
    def wrapper(*args, **kwargs):
        gen = fn(*args, **kwargs)

        def send_and_yield(value):
            try:
                next_val = gen.send(value)
            except StopIteration as e:
                result = e.value
            else:
                result = next_val.flat_map(send_and_yield)
            return result

        return send_and_yield(None)
    return wrapper
```

This implementation has the disadvantage that each function given to the `flat_map` method (i.e. `send_and_yield`) can only be called once due to a the instruction pointer of the generator.
This difference is crucial for handling monadic operations correctly and ensuring that the `do` decorator works as expected in various scenarios.

Other Python libraries that implement the do-notation:

* [https://github.com/internetimagery/do-not](https://github.com/internetimagery/do-not)
* [https://github.com/underspecified/GenMonads](https://github.com/underspecified/GenMonads)
* [https://github.com/Technologicat/unpythonic](https://github.com/Technologicat/unpythonic)
* [https://github.com/papaver/pyfnz](https://github.com/papaver/pyfnz)
