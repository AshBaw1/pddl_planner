from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

from planner.model import (
    GroundAction,
    GroundDurativeAction,
    GroundMethod,
    State,
    applicable,
    apply_action,
    is_goal,
    action_cost,
    method_applicable,
)
from planner.pddl_parser import Fact, Problem, Task
from planner.search.heuristics import (
    interval_relaxation,
    goal_count,
    cost_sensitive_goal_heuristic,
)


@dataclass
class SearchResult:
    found: bool
    plan: List
    expanded: int
    message: str


@dataclass(frozen=True)
class RunningAction:
    action: GroundDurativeAction
    start_time: float
    end_time: float


@dataclass(frozen=True)
class TemporalPlanStep:
    start_time: float
    action: GroundDurativeAction
    duration: float

    def display(self) -> str:
        return f"{self.start_time:.3f}: {self.action.display()} [{self.duration:.3f}]"


@dataclass(frozen=True)
class TemporalState:
    time: float
    facts: frozenset[Fact]
    running: Tuple[RunningAction, ...]

    def key(self):
        running_key = tuple(
            sorted(
                (
                    r.action.display(),
                    round(r.start_time, 6),
                    round(r.end_time, 6),
                )
                for r in self.running
            )
        )
        return (round(self.time, 6), self.facts, running_key)


def bfs(initial: State, actions: List[GroundAction], problem: Problem, max_expansions: int = 10000) -> SearchResult:
    queue = deque([(initial, [])])
    closed = set()
    expanded = 0

    while queue and expanded < max_expansions:
        state, plan = queue.popleft()

        if state in closed:
            continue

        if is_goal(state, problem):
            return SearchResult(True, plan, expanded, "Plan found")

        closed.add(state)
        expanded += 1

        for action in actions:
            if applicable(state, action):
                queue.append((apply_action(state, action), plan + [action]))

    return SearchResult(False, [], expanded, "No plan found")


def astar(initial: State, actions: List[GroundAction], problem: Problem, max_expansions: int = 10000) -> SearchResult:
    counter = 0
    open_list = [(goal_count(initial, problem), 0, counter, initial, [])]
    best_g = {initial: 0}
    expanded = 0

    while open_list and expanded < max_expansions:
        _, g, _, state, plan = heapq.heappop(open_list)

        if is_goal(state, problem):
            return SearchResult(True, plan, expanded, "Plan found")

        expanded += 1

        for action in actions:
            if applicable(state, action):
                ns = apply_action(state, action)
                ng = g + 1

                if ns not in best_g or ng < best_g[ns]:
                    best_g[ns] = ng
                    counter += 1
                    heapq.heappush(
                        open_list,
                        (ng + goal_count(ns, problem), ng, counter, ns, plan + [action]),
                    )

    return SearchResult(False, [], expanded, "No plan found")


def greedy_best_first(initial: State, actions: List[GroundAction], problem: Problem, max_expansions: int = 10000) -> SearchResult:
    counter = 0
    h0 = interval_relaxation(initial, problem, actions)
    open_list = [(h0, counter, initial, [])]
    closed = set()
    expanded = 0

    while open_list and expanded < max_expansions:
        _, _, state, plan = heapq.heappop(open_list)

        if state in closed:
            continue

        if is_goal(state, problem):
            return SearchResult(True, plan, expanded, "Plan found")

        closed.add(state)
        expanded += 1

        for action in actions:
            if applicable(state, action):
                ns = apply_action(state, action)

                if ns in closed:
                    continue

                counter += 1
                h = interval_relaxation(ns, problem, actions)
                heapq.heappush(open_list, (h, counter, ns, plan + [action]))

    return SearchResult(False, [], expanded, "No plan found")


def anytime_weighted_astar(
    initial: State,
    actions: List[GroundAction],
    problem: Problem,
    weight: float = 2.0,
    max_expansions: int = 10000,
) -> SearchResult:
    counter = 0
    expanded = 0

    best_plan = None
    best_solution_cost = float("inf")

    g0 = 0.0
    h0 = cost_sensitive_goal_heuristic(initial, problem, actions)

    open_list = [(g0 + weight * h0, g0, counter, initial, [])]
    best_g = {initial: 0.0}

    while open_list and expanded < max_expansions:
        _, g, _, state, plan = heapq.heappop(open_list)

        if g > best_g.get(state, float("inf")):
            continue

        if g >= best_solution_cost:
            continue

        if is_goal(state, problem):
            if g < best_solution_cost:
                best_solution_cost = g
                best_plan = plan
            continue

        expanded += 1

        for action in actions:
            if applicable(state, action):
                ns = apply_action(state, action)
                step_cost = action_cost(state, action)
                new_g = g + step_cost

                if new_g >= best_solution_cost:
                    continue

                if new_g < best_g.get(ns, float("inf")):
                    best_g[ns] = new_g
                    counter += 1

                    h = cost_sensitive_goal_heuristic(ns, problem, actions)
                    new_f = new_g + weight * h

                    heapq.heappush(open_list, (new_f, new_g, counter, ns, plan + [action]))

    if best_plan is not None:
        return SearchResult(True, best_plan, expanded, f"Best plan found with cost {best_solution_cost}")

    return SearchResult(False, [], expanded, "No plan found")


def temporal_goal_reached(facts: frozenset[Fact], problem: Problem) -> bool:
    return all(goal in facts for goal in problem.goal_facts)


def temporal_start_applicable(
    facts: frozenset[Fact],
    action: GroundDurativeAction,
    running: Tuple[RunningAction, ...],
) -> bool:
    if not all(p in facts for p in action.start_positive_preconditions):
        return False

    if not all(n not in facts for n in action.start_negative_preconditions):
        return False

    protected_facts = set()
    for r in running:
        protected_facts.update(r.action.overall_positive_preconditions)

    for delete_effect in action.start_delete_effects:
        if delete_effect in protected_facts:
            return False

    return True


def temporal_overall_conditions_hold(facts: frozenset[Fact], running: Tuple[RunningAction, ...]) -> bool:
    for r in running:
        for condition in r.action.overall_positive_preconditions:
            if condition not in facts:
                return False
    return True


def apply_start_effects(facts: frozenset[Fact], action: GroundDurativeAction) -> frozenset[Fact]:
    new_facts = set(facts)

    for delete_effect in action.start_delete_effects:
        new_facts.discard(delete_effect)

    for add_effect in action.start_add_effects:
        new_facts.add(add_effect)

    return frozenset(new_facts)


def apply_end_effects(facts: frozenset[Fact], action: GroundDurativeAction) -> frozenset[Fact]:
    new_facts = set(facts)

    for delete_effect in action.end_delete_effects:
        new_facts.discard(delete_effect)

    for add_effect in action.end_add_effects:
        new_facts.add(add_effect)

    return frozenset(new_facts)


def temporal_heuristic(facts: frozenset[Fact], problem: Problem) -> int:
    return sum(1 for goal in problem.goal_facts if goal not in facts)


def temporal_search(
    initial: State,
    actions: List[GroundDurativeAction],
    problem: Problem,
    max_expansions: int = 10000,
) -> SearchResult:
    counter = 0
    expanded = 0

    initial_temporal_state = TemporalState(
        time=0.0,
        facts=initial.facts,
        running=tuple(),
    )

    h0 = temporal_heuristic(initial_temporal_state.facts, problem)
    open_list = [(h0, 0.0, counter, initial_temporal_state, [])]
    closed = set()

    while open_list and expanded < max_expansions:
        _, makespan, _, state, plan = heapq.heappop(open_list)

        key = state.key()
        if key in closed:
            continue

        if temporal_goal_reached(state.facts, problem) and not state.running:
            return SearchResult(True, plan, expanded, "Temporal plan found")

        closed.add(key)
        expanded += 1

        if state.running:
            next_end_time = min(r.end_time for r in state.running)
            finishing = [r for r in state.running if r.end_time == next_end_time]

            facts_after_end = state.facts
            valid_end = True

            for r in finishing:
                action = r.action

                if not all(p in facts_after_end for p in action.end_positive_preconditions):
                    valid_end = False
                    break

                if not all(n not in facts_after_end for n in action.end_negative_preconditions):
                    valid_end = False
                    break

                facts_after_end = apply_end_effects(facts_after_end, action)

            if valid_end:
                remaining_running = tuple(r for r in state.running if r.end_time != next_end_time)

                if temporal_overall_conditions_hold(facts_after_end, remaining_running):
                    ns = TemporalState(
                        time=next_end_time,
                        facts=facts_after_end,
                        running=remaining_running,
                    )

                    counter += 1
                    h = temporal_heuristic(ns.facts, problem)
                    new_makespan = max(makespan, next_end_time)

                    heapq.heappush(open_list, (new_makespan + h, new_makespan, counter, ns, plan))

        for action in actions:
            if temporal_start_applicable(state.facts, action, state.running):
                facts_after_start = apply_start_effects(state.facts, action)

                new_running_action = RunningAction(
                    action=action,
                    start_time=state.time,
                    end_time=state.time + action.duration,
                )

                new_running = tuple(
                    sorted(
                        state.running + (new_running_action,),
                        key=lambda r: (r.end_time, r.action.display()),
                    )
                )

                if not temporal_overall_conditions_hold(facts_after_start, new_running):
                    continue

                ns = TemporalState(
                    time=state.time,
                    facts=facts_after_start,
                    running=new_running,
                )

                new_plan = plan + [
                    TemporalPlanStep(
                        start_time=state.time,
                        action=action,
                        duration=action.duration,
                    )
                ]

                counter += 1
                h = temporal_heuristic(ns.facts, problem)
                new_makespan = max(makespan, state.time + action.duration)

                heapq.heappush(open_list, (new_makespan + h, new_makespan, counter, ns, new_plan))

    return SearchResult(False, [], expanded, "No temporal plan found")


def is_primitive_task(task: Task, actions: List[GroundAction]) -> bool:
    return any(action.name == task[0] and action.args == task[1:] for action in actions)


def find_action_for_task(task: Task, actions: List[GroundAction]) -> GroundAction | None:
    for action in actions:
        if action.name == task[0] and action.args == task[1:]:
            return action
    return None


def find_methods_for_task(task: Task, methods: List[GroundMethod]) -> List[GroundMethod]:
    return [method for method in methods if method.task == task]


def progression_htn_search(
    initial: State,
    tasks: List[Task],
    actions: List[GroundAction],
    methods: List[GroundMethod],
    problem: Problem,
    max_expansions: int = 10000,
) -> SearchResult:
    """
    Simplified progression-based HTN planner.

    It supports:
    - primitive tasks mapped to actions;
    - compound tasks decomposed by methods;
    - total-order task lists;
    - method preconditions;
    - action execution in the current state.

    It does not support partial-order HTN yet.
    """

    queue = deque([(list(tasks), initial, [])])
    closed = set()
    expanded = 0

    while queue and expanded < max_expansions:
        task_network, state, plan = queue.popleft()

        key = (tuple(task_network), state)
        if key in closed:
            continue

        closed.add(key)
        expanded += 1

        if not task_network:
            if not problem.goal_facts or is_goal(state, problem):
                return SearchResult(True, plan, expanded, "HTN plan found")
            continue

        current_task = task_network[0]
        remaining_tasks = task_network[1:]

        action = find_action_for_task(current_task, actions)

        if action is not None:
            if applicable(state, action):
                new_state = apply_action(state, action)
                queue.append((remaining_tasks, new_state, plan + [action]))
            continue

        applicable_methods = [
            method
            for method in find_methods_for_task(current_task, methods)
            if method_applicable(state, method)
        ]

        for method in applicable_methods:
            new_tasks = list(method.subtasks) + remaining_tasks
            queue.append((new_tasks, state, plan))

    return SearchResult(False, [], expanded, "No HTN plan found")