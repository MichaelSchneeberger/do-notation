from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import wraps
import inspect
import textwrap
from typing import Any, Callable, Generator


@dataclass
class _Instructions:
    instr: list


@dataclass
class _Returned(_Instructions): ...


class do:
    def __init__(
        self,
        attr: str = "flat_map",
        callback: Callable[[Any, Callable[[Any], Any]], Any] | None = None,
        print_code: bool = False,
    ):
        
        if callback:
            callback_source = inspect.getsource(callback)
            callback_ast = ast.parse(callback_source).body[0]
            callback_name = callback_ast.name

            def to_flat_map_ast(source, nested_func, lineno):
                return ast.Call(
                    func=ast.Name(
                        id=callback_name,
                        ctx=ast.Load(),
                        lineno=0,
                        col_offset=0,
                    ),
                    args=[source, nested_func],
                    keywords=[],
                    lineno=lineno,
                    col_offset=0,
                )
        else:

            def to_flat_map_ast(source, nested_func, lineno):
                return ast.Call(
                    func=ast.Attribute(
                        value=source,
                        attr=attr,
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=0,
                    ),
                    args=[nested_func],
                    keywords=[],
                    lineno=0,
                    col_offset=0,
                )

        self.to_flat_map_ast = to_flat_map_ast
        self.print_code = print_code

    def __call__[**P, U, V](
        self,
        func: Callable[P, Generator[U, None, V]] | Callable[P, V],
    ) -> Callable[P, V]:
        
        if not inspect.isgeneratorfunction(func):
            return func

        func_source = textwrap.dedent(inspect.getsource(func))
        func_ast = ast.parse(func_source).body[0]
        func_name = func_ast.name

        # Adjust the line number in the AST to align with the original AST structure
        func_lineno = func.__code__.co_firstlineno - func_ast.lineno + 1
        ast.increment_lineno(func_ast, func_lineno)

        def get_nested_flatmap_instr(
            current_scope_instr: list,
            outer_scope_instr: list = [],
            nesting_index: int = 0,
        ) -> _Instructions:
            """
            This function traverses the given body and translates the sequence of yield statements into
            a nested `flat_map` method call sequence.

            Arguments:
            - current_scope_instr: List of instructions being traversed by the function until a yield statement
              is encountered.
            - outer_scope_instr: List of instructions that follow (possibly nested) if-else statements.
              This is used when `get_nested_flatmap_instr` is called recursively.
            - nesting_index: Index representing the current depth within the nested flat_map call stack.
            """

            n_body = []

            def _case_yield(
                yield_value, lineno, arg_name="_", n_body=n_body, assign_instr=[]
            ):
                # If the generator function does not explicitly define a return value
                # (resulting in None by Python convention), the monadic object produced
                # by the last yield statement is directly returned rather than invoking
                # a flat_map call on it.
                if (
                    len(outer_scope_instr) == 0
                    and instr_index == len(current_scope_instr) - 1
                ):
                    return_value = ast.Return(
                        value=yield_value,
                        lineno=0,
                        col_offset=0,
                    )
                    return _Returned(n_body + [return_value])

                # collect all subsequent instructions and put them inside a local function
                # called '_donotation_flatmap_func_[index]'
                n_current_scope_instr = (
                    current_scope_instr[instr_index + 1 :] + outer_scope_instr
                )
                func_body = get_nested_flatmap_instr(
                    current_scope_instr=n_current_scope_instr,
                    nesting_index=nesting_index + 1,
                )
                nested_func_name = f"_donotation_flatmap_func_{nesting_index}"

                n_body.append(
                    ast.FunctionDef(
                        name=nested_func_name,
                        args=ast.arguments(
                            posonlyargs=[],
                            args=[
                                ast.arg(
                                    arg=arg_name,
                                    lineno=0,
                                    col_offset=0,
                                )
                            ],
                            kwonlyargs=[],
                            kw_defaults=[],
                            defaults=[],
                        ),
                        body=assign_instr + func_body.instr,
                        decorator_list=[],
                        type_params=[],
                        lineno=0,
                        col_offset=0,
                    )
                )

                # call the flat_map method with the '_donotation_flatmap_func_[index]' function as an argument
                nested_func_ast = ast.Name(
                    id=nested_func_name,
                    ctx=ast.Load(),
                    lineno=0,
                    col_offset=0,
                )
                flat_map_ast = self.to_flat_map_ast(
                    yield_value, nested_func_ast, lineno
                )
                return_flat_map_call = ast.Return(
                    value=flat_map_ast,
                    lineno=0,
                    col_offset=0,
                )
                return _Returned(n_body + [return_flat_map_call])

            for instr_index, instr in enumerate(current_scope_instr):
                match instr:
                    case ast.Expr(
                        value=ast.Yield(value=yield_value, lineno=lineno)
                        | ast.YieldFrom(value=yield_value, lineno=lineno)
                    ):
                        return _case_yield(yield_value, lineno)

                    case ast.Assign(
                        targets=[ast.Name(arg_name), *_],
                        value=ast.Yield(value=yield_value)
                        | ast.YieldFrom(value=yield_value),
                        lineno=lineno,
                    ):
                        return _case_yield(yield_value, lineno, arg_name)

                    case ast.Assign(
                        targets=targets,
                        value=ast.Yield(value=yield_value)
                        | ast.YieldFrom(value=yield_value),
                        lineno=lineno,
                    ):
                        arg_name = f"_donotation_arg_name_{nesting_index}"
                        assign_instr = ast.Assign(
                            targets=targets,
                            value=ast.Name(
                                arg_name,
                                lineno=0,
                                col_offset=0,
                                ctx=ast.Load(),
                            ),
                        )
                        ast.copy_location(assign_instr, instr)
                        
                        return _case_yield(
                            yield_value,
                            lineno,
                            f"_donotation_arg_name_{nesting_index}",
                            assign_instr=[assign_instr],
                        )

                    case ast.Return():
                        return _Returned(n_body + [instr])

                    case ast.If(test, body, orelse):
                        n_outer_scope_instr = (
                            current_scope_instr[instr_index + 1 :] + outer_scope_instr
                        )

                        body_instr = get_nested_flatmap_instr(
                            current_scope_instr=body,
                            outer_scope_instr=n_outer_scope_instr,
                            nesting_index=nesting_index,
                        )
                        orelse_instr = get_nested_flatmap_instr(
                            current_scope_instr=orelse,
                            outer_scope_instr=n_outer_scope_instr,
                            nesting_index=nesting_index,
                        )

                        n_instr = ast.If(
                            test=test,
                            body=body_instr.instr,
                            orelse=orelse_instr.instr,
                        )
                        ast.copy_location(n_instr, instr)
                        n_body.append(n_instr)

                        match (body_instr, orelse_instr):
                            case (_Returned(), _Returned()):
                                return _Returned(instr=n_body)

                    case ast.Match(subject=subject, cases=cases):
                        n_outer_scope_instr = (
                            current_scope_instr[instr_index + 1 :] + outer_scope_instr
                        )

                        all_returned = [True]
                        def gen_cases():
                            for case in cases:
                                match case:
                                    case ast.match_case(pattern=pattern, guard=guard, body=body):
                                        match_instr = get_nested_flatmap_instr(
                                            current_scope_instr=body,
                                            outer_scope_instr=n_outer_scope_instr,
                                            nesting_index=nesting_index,
                                        )

                                        if not isinstance(match_instr, _Returned):
                                            all_returned[0] = False

                                        n_case = ast.match_case(
                                            pattern=pattern,
                                            guard=guard,
                                            body=match_instr.instr,
                                        )
                                        ast.copy_location(n_case, case)
                                        yield n_case

                        n_instr = ast.Match(subject=subject, cases=list(gen_cases()))
                        ast.copy_location(n_instr, instr)
                        n_body.append(n_instr)

                        if all_returned[0]:
                            return _Returned(instr=n_body)

                    case ast.For():
                        # Avoid using for loops to prevent complex variable shadowing issues.
                        raise Exception(
                            'Do not use for loops directly within a `do`-decorated generator function. '
                            'Instead, encapulate the for loop inside a separate function.'
                        )

                    case _:
                        n_body.append(instr)

            if len(outer_scope_instr) == 0:
                raise Exception(
                    f"No return statement was found when traversing the AST of function '{func_name}'. "
                    "Ensure the function either returns an object that implements a `flat_map` method "
                    "or uses a yield operation as its final instruction."
                )

            return _Instructions(n_body)

        body = get_nested_flatmap_instr(func_ast.body).instr

        dec_func_ast = ast.FunctionDef(
            name=func_name,
            args=func_ast.args,
            body=body,
            decorator_list=[],  # ignore decorators
            type_params=func_ast.type_params,
            lineno=0,
            col_offset=0,
        )

        module = ast.Module(
            body=[dec_func_ast],
            type_ignores=[],
        )

        if self.print_code:
            print(ast.unparse(module))

        code = compile(
            module,
            filename=inspect.getsourcefile(func),
            mode="exec",
        )

        # Capture the local variables of the callee at the point where the decorator is applied.
        # Any additional local variables defined after the decorator is applied cannot be included.
        locals = inspect.currentframe().f_back.f_locals

        globals = locals | func.__globals__
        exec(code, globals)
        dec_func = globals[func_name]

        assert not inspect.isgeneratorfunction(dec_func), (
            f'Unsupported yielding detected in the body of the function "{func_name}" yields not supported. '
            "Yielding operations are only allowed within if-else statements."
        )

        return wraps(func)(dec_func)  # type: ignore
