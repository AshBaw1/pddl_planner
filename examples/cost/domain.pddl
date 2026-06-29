(define (domain robot-costs)
  (:requirements :strips :typing :action-costs :numeric-fluents)

  (:types location)

  (:predicates
    (at ?l - location)
    (connected ?from ?to - location)
  )

  (:functions
    (total-cost)
    (move-cost ?from ?to - location)
  )

  (:action move
    :parameters (?from ?to - location)
    :precondition (and
      (at ?from)
      (connected ?from ?to)
    )
    :effect (and
      (not (at ?from))
      (at ?to)
      (increase (total-cost) (move-cost ?from ?to))
    )
  )
)