import ast
from dataclasses import dataclass
from functools import wraps
import inspect
from typing import Any, Callable, Generator


def _create_arg(name):
    return ast.arg(
        arg=name,
        lineno=0,
        col_offset=0,
    )


def _create_arguments(args):
    return ast.arguments(
        posonlyargs=[],
        args=args,
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[],
        lineno=0,
        col_offset=0,
    )


def _create_function(name, body, args=[]):
    return ast.FunctionDef(
        name=name,
        args=_create_arguments(args=args),
        body=body,
        decorator_list=[],
        type_params=[],
        lineno=0,
        col_offset=0,
    )


def _create_call(name, args):
    return ast.Call(
        func=_create_name(name=name),
        args=args,
        keywords=[],
        lineno=0,
        col_offset=0,
    )


def _create_method_call(attr: str, value, args):
    return ast.Call(
        func=ast.Attribute(
            value=value,
            attr=attr,
            ctx=ast.Load(),
            lineno=0,
            col_offset=0,
        ),
        args=args,
        keywords=[],
        lineno=0,
        col_offset=0,
    )


def _create_return_value(value):
    return ast.Return(
        value=value,
        lineno=0,
        col_offset=0,
    )


def _create_module(body):
    return ast.Module(
        body=body,
        type_ignores=[],
        lineno=0,
        col_offset=0,
    )


def _create_if(test, body, orelse):
    return ast.If(
        test=test,
        body=body,
        orelse=orelse,
        lineno=0,
        col_offset=0,
    )


def _create_name(name):
    return ast.Name(
        id=name,
        ctx=ast.Load(lineno=0, col_offset=0),
        lineno=0,
        col_offset=0,
    )


@dataclass
class _Instructions:
    instr: list


@dataclass
class _Returned(_Instructions): ...


def do(
    func=None,
    attr: str = "flat_map",
    callback: Callable[[Any, Callable[[Any], Any]], Any] | None = None,
):
    if callback:
        callback_source = inspect.getsource(callback)
        callback_ast = ast.parse(callback_source).body[0]
        callback_name = callback_ast.name

        def get_flat_map_ast(source, nested_func):
            return _create_call(
                name=callback_name,
                args=[source, nested_func],
            )
    else:

        def get_flat_map_ast(source, nested_func):
            return _create_method_call(attr=attr, value=source, args=[nested_func])

    def do_decorator[U](
        func: Callable[..., Generator[U, None, None]],
    ) -> Callable[..., U]:
        func_source = inspect.getsource(func)
        func_ast = ast.parse(func_source).body[0]
        func_name = func_ast.name

        def get_body_instructions(fallback_bodies, collected_bodies) -> _Instructions:
            new_body = []

            def _case_yield(new_body, yield_value, arg_name="_"):
                # is last isntruction?
                if (
                    all(len(b) == 0 for b in collected_bodies)
                    and body_index == len(fallback_bodies) - 1
                    and instr_index == len(current_body) - 1
                ):
                    return _Returned(new_body + [_create_return_value(yield_value)])

                new_fallback_bodies = (
                    collected_bodies
                    + fallback_bodies[: -body_index - 1]
                    + (current_body[instr_index + 1 :],)
                )
                func_body = get_body_instructions(new_fallback_bodies, tuple())
                nested_func_name = "_yield_func"
                new_body += [
                    _create_function(
                        name=nested_func_name,
                        body=func_body.instr,
                        args=[_create_arg(arg_name)],
                    )
                ]

                nested_func_ast = _create_name(nested_func_name)
                flat_map_ast = get_flat_map_ast(yield_value, nested_func_ast)
                return _Returned(new_body + [_create_return_value(flat_map_ast)])

            for body_index, current_body in enumerate(reversed(fallback_bodies)):
                for instr_index, instr in enumerate(current_body):
                    match instr:
                        case ast.Expr(value=ast.Yield(value=yield_value)):
                            return _case_yield(new_body, yield_value)

                        case ast.Assign(
                            targets=[ast.Name(arg_name), *_],
                            value=ast.Yield(value=yield_value),
                        ):
                            return _case_yield(new_body, yield_value, arg_name)

                        case ast.Return():
                            return _Returned(new_body + [instr])

                        case ast.If(test, body, orelse):
                            n_collected_bodies = (
                                collected_bodies
                                + fallback_bodies[: -body_index - 1]
                                + (current_body[instr_index + 1 :],)
                            )

                            body_instr = get_body_instructions(
                                (body,), n_collected_bodies
                            )
                            orelse_instr = get_body_instructions(
                                (orelse,), n_collected_bodies
                            )

                            new_body += [
                                _create_if(test, body_instr.instr, orelse_instr.instr)
                            ]

                            match (body_instr, orelse_instr):
                                case (_Returned(), _Returned()):
                                    return _Returned(instr=new_body)
                                case _:
                                    pass

                        case _:
                            new_body += [instr]

            if len(collected_bodies) == 0:
                raise Exception(
                    f'Function "{func_name}" must return a monadic object that defines a `flat_map` method. '
                    "However, it returned None."
                )

            return _Instructions(new_body)

        args = [arg.arg for arg in func_ast.args.args]
        body = get_body_instructions((func_ast.body,), tuple())

        new_func_ast = _create_function(
            name=func_name, body=body.instr, args=[_create_arg(arg) for arg in args]
        )

        # print(ast.dump(new_func_ast, indent=4))
        # print(ast.unparse(new_func_ast))

        code = compile(_create_module(body=[new_func_ast]), "", mode="exec")
        exec(code, func.__globals__)

        dec_func = func.__globals__[func_name]

        assert not inspect.isgenerator(dec_func), (
            f'Unsupported yielding detected in the body of the function "{func_name}" yields not supported. '
            "Yielding operations are only allowed within if-else statements."
        )

        return wraps(func)(dec_func)

    # See if we're being called as @do or @do().
    if func is None:
        return do_decorator

    # We're called as @do without parens.
    return do_decorator(func)
