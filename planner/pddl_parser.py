from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Union

Fact = Tuple[str, ...]
Task = Tuple[str, ...]
NumericKey = Tuple[str, ...]
NumericValue = Union[float, NumericKey]


@dataclass
class NumericCondition:
    op: str
    fluent: NumericKey
    value: NumericValue


@dataclass
class NumericEffect:
    op: str
    fluent: NumericKey
    value: NumericValue


@dataclass
class ActionSchema:
    name: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    positive_preconditions: List[Fact] = field(default_factory=list)
    negative_preconditions: List[Fact] = field(default_factory=list)
    numeric_preconditions: List[NumericCondition] = field(default_factory=list)
    add_effects: List[Fact] = field(default_factory=list)
    delete_effects: List[Fact] = field(default_factory=list)
    numeric_effects: List[NumericEffect] = field(default_factory=list)


@dataclass
class DurativeActionSchema:
    name: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    duration: float = 1.0

    start_positive_preconditions: List[Fact] = field(default_factory=list)
    start_negative_preconditions: List[Fact] = field(default_factory=list)
    overall_positive_preconditions: List[Fact] = field(default_factory=list)
    end_positive_preconditions: List[Fact] = field(default_factory=list)
    end_negative_preconditions: List[Fact] = field(default_factory=list)

    start_add_effects: List[Fact] = field(default_factory=list)
    start_delete_effects: List[Fact] = field(default_factory=list)
    end_add_effects: List[Fact] = field(default_factory=list)
    end_delete_effects: List[Fact] = field(default_factory=list)


@dataclass
class TaskSchema:
    name: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class MethodSchema:
    name: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    task: Task = tuple()
    positive_preconditions: List[Fact] = field(default_factory=list)
    negative_preconditions: List[Fact] = field(default_factory=list)
    subtasks: List[Task] = field(default_factory=list)


@dataclass
class Domain:
    name: str
    types: List[str]
    predicates: List[Fact]
    functions: List[NumericKey]
    actions: List[ActionSchema]
    durative_actions: List[DurativeActionSchema] = field(default_factory=list)
    tasks: List[TaskSchema] = field(default_factory=list)
    methods: List[MethodSchema] = field(default_factory=list)


@dataclass
class Problem:
    name: str
    domain_name: str
    objects: Dict[str, str]
    init_facts: List[Fact]
    init_numeric: Dict[NumericKey, float]
    goal_facts: List[Fact]
    goal_numeric: List[NumericCondition]
    htn_tasks: List[Task] = field(default_factory=list)


def _remove_comments(text: str) -> str:
    return re.sub(r";.*", "", text)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\(|\)|[^\s()]+", _remove_comments(text).lower())


def _parse_expr(tokens: List[str]) -> Any:
    if not tokens:
        raise ValueError("Unexpected end of input")

    token = tokens.pop(0)

    if token == "(":
        result = []
        while tokens and tokens[0] != ")":
            result.append(_parse_expr(tokens))

        if not tokens:
            raise ValueError("Missing closing parenthesis")

        tokens.pop(0)
        return result

    if token == ")":
        raise ValueError("Unexpected closing parenthesis")

    return token


def parse_sexpr(text: str) -> Any:
    tokens = _tokenize(text)
    exprs = []

    while tokens:
        exprs.append(_parse_expr(tokens))

    return exprs[0] if len(exprs) == 1 else exprs


def _typed_list(items: List[str]) -> List[Tuple[str, str]]:
    result: List[Tuple[str, str]] = []
    pending: List[str] = []
    i = 0

    while i < len(items):
        if items[i] == "-":
            typ = items[i + 1]
            for name in pending:
                result.append((name, typ))
            pending = []
            i += 2
        else:
            pending.append(items[i])
            i += 1

    for name in pending:
        result.append((name, "object"))

    return result


def _fact(expr: Any) -> Fact:
    if not isinstance(expr, list) or not expr:
        raise ValueError(f"Invalid fact: {expr}")
    return tuple(expr)


def _task(expr: Any) -> Task:
    if not isinstance(expr, list) or not expr:
        raise ValueError(f"Invalid task: {expr}")
    return tuple(expr)


def _numeric_key(expr: Any) -> NumericKey:
    if not isinstance(expr, list) or not expr:
        raise ValueError(f"Invalid numeric fluent: {expr}")
    return tuple(expr)


def _numeric_value(expr: Any) -> NumericValue:
    if isinstance(expr, list):
        return tuple(expr)
    return float(expr)


def _numeric_condition(expr: List[Any]) -> NumericCondition:
    return NumericCondition(
        op=expr[0],
        fluent=_numeric_key(expr[1]),
        value=_numeric_value(expr[2]),
    )


def _numeric_effect(expr: List[Any]) -> NumericEffect:
    return NumericEffect(
        op=expr[0],
        fluent=_numeric_key(expr[1]),
        value=_numeric_value(expr[2]),
    )


def _split_conditions(expr: Any):
    pos, neg, nums = [], [], []

    if not expr:
        return pos, neg, nums

    parts = expr[1:] if isinstance(expr, list) and expr and expr[0] == "and" else [expr]

    for part in parts:
        if isinstance(part, list) and part and part[0] == "not":
            neg.append(_fact(part[1]))
        elif isinstance(part, list) and part and part[0] in {">=", ">", "<=", "<", "="}:
            nums.append(_numeric_condition(part))
        else:
            pos.append(_fact(part))

    return pos, neg, nums


def _split_effects(expr: Any):
    adds, dels, nums = [], [], []

    if not expr:
        return adds, dels, nums

    parts = expr[1:] if isinstance(expr, list) and expr and expr[0] == "and" else [expr]

    for part in parts:
        if isinstance(part, list) and part and part[0] == "not":
            dels.append(_fact(part[1]))
        elif isinstance(part, list) and part and part[0] in {"increase", "decrease", "assign"}:
            nums.append(_numeric_effect(part))
        else:
            adds.append(_fact(part))

    return adds, dels, nums


def _parse_duration(expr: Any) -> float:
    if isinstance(expr, list) and len(expr) == 3 and expr[0] == "=":
        return float(expr[2])

    raise ValueError(f"Unsupported duration expression: {expr}")


def _split_temporal_conditions(expr: Any):
    start_pos, start_neg = [], []
    overall_pos = []
    end_pos, end_neg = [], []

    if not expr:
        return start_pos, start_neg, overall_pos, end_pos, end_neg

    parts = expr[1:] if isinstance(expr, list) and expr and expr[0] == "and" else [expr]

    for part in parts:
        if not isinstance(part, list) or len(part) < 2:
            continue

        timing = part[0]

        if timing == "at" and part[1] == "start":
            cond = part[2]
            if isinstance(cond, list) and cond and cond[0] == "not":
                start_neg.append(_fact(cond[1]))
            else:
                start_pos.append(_fact(cond))

        elif timing == "at" and part[1] == "end":
            cond = part[2]
            if isinstance(cond, list) and cond and cond[0] == "not":
                end_neg.append(_fact(cond[1]))
            else:
                end_pos.append(_fact(cond))

        elif timing == "over" and part[1] == "all":
            overall_pos.append(_fact(part[2]))

    return start_pos, start_neg, overall_pos, end_pos, end_neg


def _split_temporal_effects(expr: Any):
    start_adds, start_dels = [], []
    end_adds, end_dels = [], []

    if not expr:
        return start_adds, start_dels, end_adds, end_dels

    parts = expr[1:] if isinstance(expr, list) and expr and expr[0] == "and" else [expr]

    for part in parts:
        if not isinstance(part, list) or len(part) < 3:
            continue

        timing = part[0]

        if timing == "at" and part[1] == "start":
            effect = part[2]
            if isinstance(effect, list) and effect and effect[0] == "not":
                start_dels.append(_fact(effect[1]))
            else:
                start_adds.append(_fact(effect))

        elif timing == "at" and part[1] == "end":
            effect = part[2]
            if isinstance(effect, list) and effect and effect[0] == "not":
                end_dels.append(_fact(effect[1]))
            else:
                end_adds.append(_fact(effect))

    return start_adds, start_dels, end_adds, end_dels


def _parse_subtasks(expr: Any) -> List[Task]:
    """
    Supports HDDL-style subtasks:

    :subtasks (and
      (t1 (find-venue ?c))
      (t2 (reserve-venue ?c))
    )

    It ignores the task ids t1, t2 and keeps the listed order.
    """

    subtasks: List[Task] = []

    if not expr:
        return subtasks

    parts = expr[1:] if isinstance(expr, list) and expr and expr[0] == "and" else [expr]

    for part in parts:
        if isinstance(part, list) and len(part) == 2 and isinstance(part[1], list):
            subtasks.append(_task(part[1]))
        elif isinstance(part, list):
            subtasks.append(_task(part))

    return subtasks


def _parse_htn_tasks(expr: Any) -> List[Task]:
    """
    Supports:

    (:htn
      :tasks (and
        (t1 (organize-conference ai-conf))
      )
    )
    """

    tasks: List[Task] = []

    if not expr:
        return tasks

    i = 1
    while i < len(expr):
        key = expr[i]
        value = expr[i + 1]

        if key == ":tasks":
            tasks = _parse_subtasks(value)

        i += 2

    return tasks


def parse_domain(path: str) -> Domain:
    root = parse_sexpr(open(path, encoding="utf-8").read())

    if root[0] != "define":
        raise ValueError("Expected define")

    name = root[1][1]
    types: List[str] = ["object"]
    predicates: List[Fact] = []
    functions: List[NumericKey] = []
    actions: List[ActionSchema] = []
    durative_actions: List[DurativeActionSchema] = []
    tasks: List[TaskSchema] = []
    methods: List[MethodSchema] = []

    for section in root[2:]:
        if not isinstance(section, list) or not section:
            continue

        tag = section[0]

        if tag == ":types":
            types.extend(x for x in section[1:] if x != "-")

        elif tag == ":predicates":
            predicates = [tuple(predicate) for predicate in section[1:]]

        elif tag == ":functions":
            functions = [
                tuple(function)
                for function in section[1:]
                if isinstance(function, list)
            ]

        elif tag == ":action":
            action = ActionSchema(name=section[1])
            i = 2

            while i < len(section):
                key = section[i]
                value = section[i + 1]

                if key == ":parameters":
                    action.parameters = _typed_list(value)
                elif key == ":precondition":
                    (
                        action.positive_preconditions,
                        action.negative_preconditions,
                        action.numeric_preconditions,
                    ) = _split_conditions(value)
                elif key == ":effect":
                    (
                        action.add_effects,
                        action.delete_effects,
                        action.numeric_effects,
                    ) = _split_effects(value)

                i += 2

            actions.append(action)

        elif tag == ":durative-action":
            action = DurativeActionSchema(name=section[1])
            i = 2

            while i < len(section):
                key = section[i]
                value = section[i + 1]

                if key == ":parameters":
                    action.parameters = _typed_list(value)
                elif key == ":duration":
                    action.duration = _parse_duration(value)
                elif key == ":condition":
                    (
                        action.start_positive_preconditions,
                        action.start_negative_preconditions,
                        action.overall_positive_preconditions,
                        action.end_positive_preconditions,
                        action.end_negative_preconditions,
                    ) = _split_temporal_conditions(value)
                elif key == ":effect":
                    (
                        action.start_add_effects,
                        action.start_delete_effects,
                        action.end_add_effects,
                        action.end_delete_effects,
                    ) = _split_temporal_effects(value)

                i += 2

            durative_actions.append(action)

        elif tag == ":task":
            task_schema = TaskSchema(name=section[1])
            i = 2

            while i < len(section):
                key = section[i]
                value = section[i + 1]

                if key == ":parameters":
                    task_schema.parameters = _typed_list(value)

                i += 2

            tasks.append(task_schema)

        elif tag == ":method":
            method = MethodSchema(name=section[1])
            i = 2

            while i < len(section):
                key = section[i]
                value = section[i + 1]

                if key == ":parameters":
                    method.parameters = _typed_list(value)

                elif key == ":task":
                    method.task = _task(value)

                elif key == ":precondition":
                    (
                        method.positive_preconditions,
                        method.negative_preconditions,
                        _,
                    ) = _split_conditions(value)

                elif key == ":subtasks":
                    method.subtasks = _parse_subtasks(value)

                # :ordering is intentionally ignored in this educational version.
                i += 2

            methods.append(method)

    return Domain(
        name,
        types,
        predicates,
        functions,
        actions,
        durative_actions,
        tasks,
        methods,
    )


def parse_problem(path: str) -> Problem:
    root = parse_sexpr(open(path, encoding="utf-8").read())

    name = root[1][1]
    domain_name = ""
    objects: Dict[str, str] = {}
    init_facts: List[Fact] = []
    init_numeric: Dict[NumericKey, float] = {}
    goal_facts: List[Fact] = []
    goal_numeric: List[NumericCondition] = []
    htn_tasks: List[Task] = []

    for section in root[2:]:
        tag = section[0]

        if tag == ":domain":
            domain_name = section[1]

        elif tag == ":objects":
            for obj, typ in _typed_list(section[1:]):
                objects[obj] = typ

        elif tag == ":init":
            for item in section[1:]:
                if isinstance(item, list) and item and item[0] == "=":
                    init_numeric[_numeric_key(item[1])] = float(item[2])
                else:
                    init_facts.append(_fact(item))

        elif tag == ":goal":
            goal_facts, _, goal_numeric = _split_conditions(section[1])

        elif tag == ":htn":
            htn_tasks = _parse_htn_tasks(section)

    return Problem(
        name,
        domain_name,
        objects,
        init_facts,
        init_numeric,
        goal_facts,
        goal_numeric,
        htn_tasks,
    )