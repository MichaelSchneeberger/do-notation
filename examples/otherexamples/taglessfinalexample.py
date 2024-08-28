from abc import abstractmethod
from typing import Callable

from donotation import do


class FlatMapMixin:
    @abstractmethod
    def apply(self): ...

    @abstractmethod
    def flat_map(self, fn: Callable): ...


# define abstract operations implemented by an interpreter
class IOOperations:
    @abstractmethod
    def readln(self, prompt: str) -> FlatMapMixin: ...

    @abstractmethod
    def println(self, line: str) -> FlatMapMixin: ...


# define the program that is executed by an interpreter
@do()
def program_(op: IOOperations):
    name = yield op.readln("What is your name? ")
    age = yield op.readln("What is your age? ")
    return op.println(f"Your name is {name} and you are {age} years old!")


# define the writer monad defining some lazy evaluation
class Writer(FlatMapMixin):
    def map(self, fn: Callable):
        outer_self = self

        class MapApplicable(Writer):
            def apply(self):
                return fn(outer_self.apply())

        return MapApplicable()

    def flat_map(self, fn: Callable):
        outer_self = self

        class FlatMapApplicable(Writer):
            def apply(self):
                return fn(outer_self.apply()).apply()

        return FlatMapApplicable()

    @classmethod
    def from_(cls, val):
        class FromApplicable(Writer):
            def apply(self):
                return val

        return FromApplicable()


# define an interpreter that perform IO actions
class IOOperationsInterpreter(IOOperations):
    def readln(self, prompt: str):
        return Writer.from_(prompt).map(lambda msg: input(msg))

    def println(self, line: str):
        def fn(msg):
            print(msg)
            return msg

        return Writer.from_(line).map(fn)


interpreter = IOOperationsInterpreter()

# run the program with the IO interpreter
program_(interpreter).apply()
