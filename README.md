# Donotation

Donotation is a Python package that introduces Haskell-like do notation using a Python decorator. 

## Features

* Haskell-like Behavior: Emulate Haskell's do notation for Python objects that implement the `flat_map` method.
* Syntactic sugar: Use the `@do` decorator to convert generator functions into nested `flat_map` method calls by using the Abstract Syntax Tree (AST).
* Simplified Syntax: Write complex monadic `flat_map` sequences in a clean and readable way without needing to define auxillary functions.

## Installation

You can install Donotation using pip:

```
pip install donotation
```

## Usage

### Basic Example

First, import the `@do` decorator from the donotation package. Then, define a class implementing the `flat_map` method to represent the monadic operations. Finally, use the `@do` decorator on the generator function that yields objects of this class.

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
    x = yield collect_even_numbers(init+1)
    y = yield collect_even_numbers(init*x+1)
    z = yield collect_even_numbers(x*y+1)
    return collect_even_numbers(y*z+1)

state = set[int]()
state, value = example(3).func(state)
print(state)   # Output will be {4, 690}
```

In this example, we define a `StateMonad` class that implements a `flat_map` method to represent a state monad.
The helper method `collect_even_numbers` is used to generate a sequence of monadic operations within the generator function `example`, which stores the immediate values if they are even integer.
The `@do` decorator converts the generator function `example` into a sequence of `flat_map` calls on the `StateMonad` objects. 


### How It Works

The `@do` decorator works by substituting the yield statements with nested `flat_map` calls using the Abstract Syntax Tree (AST) of the generator function. Here’s a breakdown of the process:

1. AST traversal: Traverse the AST of the generator function to inspect all statements.
2. Yield operation: When an yield operations is encountered, define an nested function containing the remaining statements. This nested function is then called within the `flat_map` method call.
3. If-else statements: If an if-else statement is encountered, traverse its AST to inspect all statements. If an yield statement is found, the nested function for the `flat_map` method includes the rest of the if-else statement and the remaining statements of the generator function.

### Yield Placement Restrictions

The yield operations within the generator can only be placed within if-else statements but not within for or while statements. Yield statements within the for or while statement are not substituted by a monadic `flat_map` chaining, resulting in a generator function due to the leftover yield statements. In this case, an exception is raised.

#### Good Example

Here’s a good example where the yield statement is only placed within if-else statements:

``` python
@do()
def good_example():
    if condition:
        x = yield Monad(1)
    else:
        x = yield Monad(2)
    y = yield Monad(x + 1)
    return Monad(y + 1)

result = good_example()
```

#### Bad Example

Here’s a bad example where the yield statement is placed within a for or while statement:

``` python
@do()
def bad_example():
    for i in range(3):
        x = yield Monad(i)
    return Monad(x + 1)

# This will raise an exception due to improper yield placement
result = bad_example()
```

### Customization

The `@do` decorator can be customized to work with different implementations of the flat map operation.
There are two ways to change the bheavior of the `@do` decorator:

#### Custom Mehtod Name:

If the method is called "bind" instead of "flat_map", you can specify the method name when creating the decorator instance:

``` python
my_do = do(attr='bind')

@my_do()  # converts the generator function to nested `bind` method calls
def bad_example():
    for i in range(3):
        x = yield Monad(i)
    return Monad(x + 1)
```

#### External Flat Map Function:

If the flat map operation is defined as an external function rather than a method of the class, you can define a callback function:

``` python
flat_map = ...  # some implementation of the flat map operation

def callback(source, fn):
    return flat_map(source, fn)

my_do = do(callback=callback)

@my_do()  # calls the callback to perform a flat map operation
def bad_example():
    for i in range(3):
        x = yield Monad(i)
    return Monad(x + 1)
```

In both cases, the `@do` decorator adapts to the specified method name or external function, allowing for flexible integration with different monadic structures.


## Decorator Implementation

Here is the pseudo-code of the `@do` decorator:

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

The provided code is a pseudo-code implementation that illustrates the core concept of the `@do` decorator. 
The main difference between this pseudo-code and the actual implementation is that the function given to the `flat_map` method can only be called once in the pseudo-code, whereas in the real implementation, that function can be called arbitrarily many times.
This distinction is crucial for handling monadic operations correctly and ensuring that the `@do` decorator works as expected in various scenarios.


### Translating a Generator Function to nested `flat_map` Calls

To better understand how the `@do` decorator translates a generator function into a nested sequence of `flat_map` calls, let's consider the following example function:

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

This translation shows how each yield in the generator function corresponds to a `flat_map` call that takes a lambda function, chaining the monadic operations together.
