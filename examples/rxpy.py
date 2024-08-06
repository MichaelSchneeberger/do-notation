import rx

from donotation import do
from rx import operators as op


def callback(source, fn):
    return source.pipe(
        op.flat_map(fn),
    )


# define new do decorator applying custom flat_map operation using a callback
rx_do = do(callback=callback)


@rx_do
def rx_action():
    v = yield rx.from_([1, 2, 3, 4])

    if v % 2 == 0:
        return rx.from_(list(range(v)))
    else:
        return rx.empty()


rx_action().subscribe(print) # Output will be 0 1 0 1 2 3
