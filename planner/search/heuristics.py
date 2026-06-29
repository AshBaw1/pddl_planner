from __future__ import annotations

from planner.model import State
from planner.pddl_parser import Problem


INF = 10**9


def goal_count(state: State, problem: Problem) -> int:
    """
    Simple fallback heuristic.
    Counts how many goal conditions are not currently satisfied.
    """
    nums = state.numeric_dict()
    missing = 0

    for goal in problem.goal_facts:
        if goal not in state.facts:
            missing += 1

    for cond in problem.goal_numeric:
        value = nums.get(cond.fluent, 0.0)

        if cond.op == ">=" and not value >= cond.value:
            missing += 1
        elif cond.op == ">" and not value > cond.value:
            missing += 1
        elif cond.op == "<=" and not value <= cond.value:
            missing += 1
        elif cond.op == "<" and not value < cond.value:
            missing += 1
        elif cond.op == "=" and not value == cond.value:
            missing += 1

    return missing


def interval_relaxation(
    state: State,
    problem: Problem,
    actions,
    max_levels: int = 20,
) -> int:
    """
    Simplified interval-based relaxation heuristic for numeric planning.

    Returns:
        0, 1, 2, ...  number of relaxed expansion levels needed
        INF           goal not reachable within max_levels
    """

    nums = state.numeric_dict()

    intervals = {
        fluent: [value, value]
        for fluent, value in nums.items()
    }

    reachable_facts = set(state.facts)

    if relaxed_goal_reached(reachable_facts, intervals, problem):
        return 0

    for level in range(1, max_levels + 1):
        changed = False

        for action in actions:
            if not relaxed_action_applicable(action, reachable_facts, intervals):
                continue

            # Add positive effects.
            # Delete effects are ignored in the relaxed problem.
            for fact in action.add_effects:
                if fact not in reachable_facts:
                    reachable_facts.add(fact)
                    changed = True

            # Expand numeric intervals.
            for effect in action.numeric_effects:
                fluent = effect.fluent

                if fluent not in intervals:
                    intervals[fluent] = [0.0, 0.0]

                old_min, old_max = intervals[fluent]
                value_min, value_max = resolve_interval_value(effect.value, intervals)

                if effect.op == "increase":
                    new_min = old_min
                    new_max = old_max + value_max

                elif effect.op == "decrease":
                    new_min = old_min - value_max
                    new_max = old_max

                elif effect.op == "assign":
                    new_min = min(old_min, value_min)
                    new_max = max(old_max, value_max)

                else:
                    continue

        if relaxed_goal_reached(reachable_facts, intervals, problem):
            return level

        if not changed:
            break

    return INF


def relaxed_action_applicable(action, reachable_facts, intervals) -> bool:
    """
    Checks whether an action may be applicable in the relaxed interval state.

    In this relaxed heuristic:
    - positive preconditions must be reachable;
    - negative preconditions are ignored;
    - numeric preconditions must be possible within the interval.
    """

    for precondition in action.positive_preconditions:
        if precondition not in reachable_facts:
            return False

    for condition in action.numeric_preconditions:
        if not interval_satisfies_condition(intervals, condition):
            return False

    return True


def relaxed_goal_reached(reachable_facts, intervals, problem) -> bool:
    """
    Checks whether the goal is reachable in the relaxed interval state.
    """

    for goal in problem.goal_facts:
        if goal not in reachable_facts:
            return False

    for condition in problem.goal_numeric:
        if not interval_satisfies_condition(intervals, condition):
            return False

    return True


def interval_satisfies_condition(intervals, condition) -> bool:
    if condition.fluent not in intervals:
        return False

    low, high = intervals[condition.fluent]
    target_low, target_high = resolve_interval_value(condition.value, intervals)

    if condition.op == ">=":
        return high >= target_low

    if condition.op == ">":
        return high > target_low

    if condition.op == "<=":
        return low <= target_high

    if condition.op == "<":
        return low < target_high

    if condition.op == "=":
        return low <= target_high and target_low <= high

    return False


def resolve_interval_value(value, intervals):
    """
    Converts either:
      10.0
    or:
      ("fuel-required", "a", "b")

    into an interval [low, high].
    """

    if isinstance(value, tuple):
        return intervals.get(value, (0.0, 0.0))

    return value, value

def cost_sensitive_goal_heuristic(state: State, problem: Problem, actions) -> float:
    """
    Simple cost-sensitive heuristic.

    For each unsatisfied goal fact, find actions that can add it.
    The heuristic returns the maximum cheapest cost among missing goals.

    This is simple and usually underestimates the remaining cost.
    """

    missing_goals = [
        goal for goal in problem.goal_facts
        if goal not in state.facts
    ]

    if not missing_goals:
        return 0.0

    nums = state.numeric_dict()
    estimates = []

    for goal in missing_goals:
        achiever_costs = []

        for action in actions:
            if goal in action.add_effects:
                achiever_costs.append(action_cost_from_state(state, action))

        if achiever_costs:
            estimates.append(min(achiever_costs))
        else:
            estimates.append(float("inf"))

    return max(estimates)

def action_cost_from_state(state: State, action) -> float:
    nums = state.numeric_dict()

    for effect in action.numeric_effects:
        if effect.op == "increase" and effect.fluent == ("total-cost",):
            value = effect.value

            if isinstance(value, tuple):
                return nums.get(value, 0.0)

            return value

    return 1.0