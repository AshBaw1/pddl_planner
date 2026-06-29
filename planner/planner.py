from __future__ import annotations

from planner.model import (
    State,
    ground_actions,
    ground_durative_actions,
    ground_methods,
    ground_htn_tasks,
)
from planner.pddl_parser import parse_domain, parse_problem
from planner.search.algorithms import (
    astar,
    bfs,
    greedy_best_first,
    anytime_weighted_astar,
    temporal_search,
    progression_htn_search,
)


def solve(
    domain_path: str,
    problem_path: str,
    algorithm: str = "bfs",
    max_expansions: int = 10000,
):
    domain = parse_domain(domain_path)
    problem = parse_problem(problem_path)
    initial = State.from_problem(problem)

    if algorithm == "temporal":
        actions = ground_durative_actions(domain, problem)
        result = temporal_search(initial, actions, problem, max_expansions)

    elif algorithm == "htn":
        actions = ground_actions(domain, problem)
        methods = ground_methods(domain, problem)
        tasks = ground_htn_tasks(problem)

        result = progression_htn_search(
            initial,
            tasks,
            actions,
            methods,
            problem,
            max_expansions,
        )

    else:
        actions = ground_actions(domain, problem)

        if algorithm == "bfs":
            result = bfs(initial, actions, problem, max_expansions)

        elif algorithm == "astar":
            result = astar(initial, actions, problem, max_expansions)

        elif algorithm in {"gbfs", "best-first", "greedy"}:
            result = greedy_best_first(initial, actions, problem, max_expansions)

        elif algorithm == "anytime-wa":
            result = anytime_weighted_astar(
                initial,
                actions,
                problem,
                max_expansions=max_expansions,
            )

        else:
            raise ValueError(
                "Algorithm must be bfs, astar, gbfs, anytime-wa, temporal, or htn"
            )

    return domain, problem, actions, result