(define (domain robot-navigation)
  (:requirements :strips :typing)

  (:types robot location)

  (:predicates
    (at ?r - robot ?l - location)
    (connected ?from - location ?to - location)
  )

  (:action move
    :parameters (?r - robot ?from - location ?to - location)
    :precondition (and
      (at ?r ?from)
      (connected ?from ?to)
    )
    :effect (and
      (not (at ?r ?from))
      (at ?r ?to)
    )
  )
)
