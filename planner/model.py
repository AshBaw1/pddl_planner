from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, FrozenSet, List, Tuple

from .pddl_parser import (
    Domain,
    Fact,
    Task,
    NumericCondition,
    NumericEffect,
    NumericKey,
    NumericValue,
    Problem,
)


@dataclass(frozen=True)
class State:
    facts: FrozenSet[Fact]
    numeric: Tuple[Tuple[NumericKey, float], ...]

    @staticmethod
    def from_problem(problem: Problem) -> "State":
        return State(
            frozenset(problem.init_facts),
            tuple(sorted(problem.init_numeric.items())),
        )

    def numeric_dict(self) -> Dict[NumericKey, float]:
        return dict(self.numeric)


@dataclass(frozen=True)
class GroundAction:
    name: str
    args: Tuple[str, ...]
    positive_preconditions: Tuple[Fact, ...]
    negative_preconditions: Tuple[Fact, ...]
    numeric_preconditions: Tuple[NumericCondition, ...]
    add_effects: Tuple[Fact, ...]
    delete_effects: Tuple[Fact, ...]
    numeric_effects: Tuple[NumericEffect, ...]

    def display(self) -> str:
        return f"({self.name} {' '.join(self.args)})" if self.args else f"({self.name})"


@dataclass(frozen=True)
class GroundDurativeAction:
    name: str
    args: Tuple[str, ...]
    duration: float

    start_positive_preconditions: Tuple[Fact, ...]
    start_negative_preconditions: Tuple[Fact, ...]
    overall_positive_preconditions: Tuple[Fact, ...]
    end_positive_preconditions: Tuple[Fact, ...]
    end_negative_preconditions: Tuple[Fact, ...]

    start_add_effects: Tuple[Fact, ...]
    start_delete_effects: Tuple[Fact, ...]
    end_add_effects: Tuple[Fact, ...]
    end_delete_effects: Tuple[Fact, ...]

    def display(self) -> str:
        return f"({self.name} {' '.join(self.args)})" if self.args else f"({self.name})"


@dataclass(frozen=True)
class GroundMethod:
    name: str
    task: Task
    positive_preconditions: Tuple[Fact, ...]
    negative_preconditions: Tuple[Fact, ...]
    subtasks: Tuple[Task, ...]

    def display(self) -> str:
        return self.name


def _sub_fact(fact: Fact, env: Dict[str, str]) -> Fact:
    return tuple(env.get(x, x) for x in fact)


def _sub_task(task: Task, env: Dict[str, str]) -> Task:
    return tuple(env.get(x, x) for x in task)


def _sub_numeric_value(value: NumericValue, env: Dict[str, str]) -> NumericValue:
    if isinstance(value, tuple):
        return tuple(env.get(x, x) for x in value)
    return value


def _sub_num_cond(cond: NumericCondition, env: Dict[str, str]) -> NumericCondition:
    return NumericCondition(
        cond.op,
        tuple(env.get(x, x) for x in cond.fluent),
        _sub_numeric_value(cond.value, env),
    )


def _sub_num_eff(eff: NumericEffect, env: Dict[str, str]) -> NumericEffect:
    return NumericEffect(
        eff.op,
        tuple(env.get(x, x) for x in eff.fluent),
        _sub_numeric_value(eff.value, env),
    )


def _objects_by_type(problem: Problem) -> Dict[str, List[str]]:
    objects_by_type: Dict[str, List[str]] = {
        "object": list(problem.objects.keys())
    }

    for obj, typ in problem.objects.items():
        objects_by_type.setdefault(typ, []).append(obj)

    return objects_by_type


def ground_actions(domain: Domain, problem: Problem) -> List[GroundAction]:
    objects_by_type = _objects_by_type(problem)
    grounded: List[GroundAction] = []

    for action in domain.actions:
        domains = [
            objects_by_type.get(typ, objects_by_type["object"])
            for _, typ in action.parameters
        ]

        for combo in product(*domains):
            env = {
                var: val
                for (var, _), val in zip(action.parameters, combo)
            }

            grounded.append(
                GroundAction(
                    action.name,
                    tuple(combo),
                    tuple(_sub_fact(f, env) for f in action.positive_preconditions),
                    tuple(_sub_fact(f, env) for f in action.negative_preconditions),
                    tuple(_sub_num_cond(c, env) for c in action.numeric_preconditions),
                    tuple(_sub_fact(f, env) for f in action.add_effects),
                    tuple(_sub_fact(f, env) for f in action.delete_effects),
                    tuple(_sub_num_eff(e, env) for e in action.numeric_effects),
                )
            )

    return grounded


def ground_durative_actions(domain: Domain, problem: Problem) -> List[GroundDurativeAction]:
    objects_by_type = _objects_by_type(problem)
    grounded: List[GroundDurativeAction] = []

    for action in domain.durative_actions:
        domains = [
            objects_by_type.get(typ, objects_by_type["object"])
            for _, typ in action.parameters
        ]

        for combo in product(*domains):
            env = {
                var: val
                for (var, _), val in zip(action.parameters, combo)
            }

            grounded.append(
                GroundDurativeAction(
                    action.name,
                    tuple(combo),
                    action.duration,
                    tuple(_sub_fact(f, env) for f in action.start_positive_preconditions),
                    tuple(_sub_fact(f, env) for f in action.start_negative_preconditions),
                    tuple(_sub_fact(f, env) for f in action.overall_positive_preconditions),
                    tuple(_sub_fact(f, env) for f in action.end_positive_preconditions),
                    tuple(_sub_fact(f, env) for f in action.end_negative_preconditions),
                    tuple(_sub_fact(f, env) for f in action.start_add_effects),
                    tuple(_sub_fact(f, env) for f in action.start_delete_effects),
                    tuple(_sub_fact(f, env) for f in action.end_add_effects),
                    tuple(_sub_fact(f, env) for f in action.end_delete_effects),
                )
            )

    return grounded


def ground_methods(domain: Domain, problem: Problem) -> List[GroundMethod]:
    objects_by_type = _objects_by_type(problem)
    grounded: List[GroundMethod] = []

    for method in domain.methods:
        domains = [
            objects_by_type.get(typ, objects_by_type["object"])
            for _, typ in method.parameters
        ]

        for combo in product(*domains):
            env = {
                var: val
                for (var, _), val in zip(method.parameters, combo)
            }

            grounded.append(
                GroundMethod(
                    method.name,
                    _sub_task(method.task, env),
                    tuple(_sub_fact(f, env) for f in method.positive_preconditions),
                    tuple(_sub_fact(f, env) for f in method.negative_preconditions),
                    tuple(_sub_task(t, env) for t in method.subtasks),
                )
            )

    return grounded


def ground_htn_tasks(problem: Problem) -> List[Task]:
    return list(problem.htn_tasks)


def _resolve_numeric_value(value: NumericValue, nums: Dict[NumericKey, float]) -> float:
    if isinstance(value, tuple):
        return nums.get(value, 0.0)
    return value


def _check_numeric(value: float, op: str, target: float) -> bool:
    if op == ">=":
        return value >= target
    if op == ">":
        return value > target
    if op == "<=":
        return value <= target
    if op == "<":
        return value < target
    if op == "=":
        return value == target

    raise ValueError(f"Unknown numeric operator: {op}")


def is_goal(state: State, problem: Problem) -> bool:
    nums = state.numeric_dict()

    return all(g in state.facts for g in problem.goal_facts) and all(
        _check_numeric(
            nums.get(c.fluent, 0.0),
            c.op,
            _resolve_numeric_value(c.value, nums),
        )
        for c in problem.goal_numeric
    )


def applicable(state: State, action: GroundAction) -> bool:
    nums = state.numeric_dict()

    return (
        all(p in state.facts for p in action.positive_preconditions)
        and all(n not in state.facts for n in action.negative_preconditions)
        and all(
            _check_numeric(
                nums.get(c.fluent, 0.0),
                c.op,
                _resolve_numeric_value(c.value, nums),
            )
            for c in action.numeric_preconditions
        )
    )


def method_applicable(state: State, method: GroundMethod) -> bool:
    return (
        all(p in state.facts for p in method.positive_preconditions)
        and all(n not in state.facts for n in method.negative_preconditions)
    )


def apply_action(state: State, action: GroundAction) -> State:
    facts = set(state.facts)

    for delete_effect in action.delete_effects:
        facts.discard(delete_effect)

    for add_effect in action.add_effects:
        facts.add(add_effect)

    nums = state.numeric_dict()

    for effect in action.numeric_effects:
        current = nums.get(effect.fluent, 0.0)
        amount = _resolve_numeric_value(effect.value, nums)

        if effect.op == "increase":
            nums[effect.fluent] = current + amount

        elif effect.op == "decrease":
            nums[effect.fluent] = current - amount

        elif effect.op == "assign":
            nums[effect.fluent] = amount

    return State(
        frozenset(facts),
        tuple(sorted(nums.items())),
    )


def action_cost(state: State, action: GroundAction) -> float:
    nums = state.numeric_dict()

    for effect in action.numeric_effects:
        if effect.op == "increase" and effect.fluent == ("total-cost",):
            return _resolve_numeric_value(effect.value, nums)

    return 1.0