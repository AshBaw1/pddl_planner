

## Run classical example

```bash
python3 main.py examples/classical/robot/domain.pddl examples/classical/robot/problem.pddl --algorithm bfs
```

or:

```bash
python3 main.py examples/classical/robot/domain.pddl examples/classical/robot/problem.pddl --algorithm astar
```

## Run numeric resource example

```bash
python3 main.py examples/numeric/fuel/domain.pddl examples/numeric/fuel/problem.pddl --algorithm gbfs
```

## Run actions with costs example
python3 main.py examples/cost/domain.pddl examples/cost/problem.pddl --algorithm anytime-wa


## Run durative actions example
python3 main.py examples/temporal/domain.pddl examples/temporal/problem.pddl --algorithm temporal



## Documentation: 

educational_planner/
│
├── main.py
│   Command-line entry point.
│   Runs the planner with:
│   python3 main.py domain.pddl problem.pddl --algorithm bfs|astar|gbfs|anytime-wa|temporal|htn
│
├── planner/
│   ├── pddl_parser.py
│   │   Parses simplified PDDL/HDDL:
│   │   classical actions, numeric fluents, action costs, durative actions,
│   │   HTN tasks, methods, subtasks, and initial HTN task networks.
│   │
│   ├── model.py
│   │   Defines State, GroundAction, GroundDurativeAction, and GroundMethod.
│   │   Handles grounding, applicability checks, applying effects,
│   │   action costs, method applicability, and HTN task grounding.
│   │
│   ├── planner.py
│   │   Connects parser, grounding, and chosen algorithm.
│   │
│   └── search/
│       ├── algorithms.py
│       │   Contains BFS, A*, Greedy Best-First, Anytime Weighted A*,
│       │   temporal search, and progression-based HTN search.
│       │
│       └── heuristics.py
│           Contains goal-count heuristic, interval-relaxation heuristic,
│           and cost-sensitive heuristic.
│
└── examples/
    ├── classical/
    ├── numeric/
    │   Limited/consumable resources, e.g. fuel.
    ├── cost/
    │   Action costs using total-cost and move-cost.
    ├── temporal/
    │   Durative actions such as load, drive, unload.
    └── htn/
        HDDL-style hierarchical planning with tasks, methods, and subtasks.


Algorithms implemented:

Classical planning:
- BFS
- A* with goal-count heuristic

Numeric planning:
- Greedy Best-First Search
- Interval-based relaxation heuristic

Action-cost planning:
- Anytime Weighted A*
- Cost-sensitive goal heuristic
- Uses total-cost as accumulated action cost

Temporal planning:
- Simplified POPF-style temporal search
- Supports durative actions, at-start effects, at-end effects, and over-all conditions
- Produces temporal plans with start time and duration

HTN planning:
- Progression-based HTN search
- Supports primitive tasks, compound tasks, methods, and total-order subtasks
- Decomposes high-level tasks into executable primitive actions
- Simplified HDDL support; ordering constraints are treated by listed subtask order

