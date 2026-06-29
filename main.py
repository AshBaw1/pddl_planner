import argparse
from planner.planner import solve


def main():
    parser = argparse.ArgumentParser(description="Mini Educational PDDL Planner")
    parser.add_argument("domain")
    parser.add_argument("problem")
    parser.add_argument(
        "--algorithm",
        choices=["bfs", "astar", "gbfs", "anytime-wa", "temporal", "htn"],
        default="bfs",
    )
    parser.add_argument("--max-expansions", type=int, default=10000)
    args = parser.parse_args()

    domain, problem, actions, result = solve(
        args.domain,
        args.problem,
        args.algorithm,
        args.max_expansions,
    )

    print(f"Domain: {domain.name}")
    print(f"Problem: {problem.name}")
    print(f"Ground actions: {len(actions)}")
    print(f"Algorithm: {args.algorithm.upper()}")
    print(f"Expanded states: {result.expanded}")

    if result.found:
        print(result.message)
        print(f"Plan found with {len(result.plan)} step(s):")

        for i, action in enumerate(result.plan, 1):
            print(f"{i}. {action.display()}")
    else:
        print(result.message)


if __name__ == "__main__":
    main()