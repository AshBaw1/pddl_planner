(define (domain numeric-delivery)
  (:requirements :strips :typing :numeric-fluents)

  (:types robot package location)

  (:predicates
    (at ?r - robot ?l - location)
    (package-at ?p - package ?l - location)
    (carrying ?r - robot ?p - package)
    (delivered ?p - package)
    (road ?from ?to - location)
    (gas-station ?l - location)
  )

  (:functions
    (fuel ?r - robot)
    (fuel-required ?from ?to - location)
    (refuel-amount ?l - location)
  )

  (:action load
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and
      (at ?r ?l)
      (package-at ?p ?l)
    )
    :effect (and
      (carrying ?r ?p)
      (not (package-at ?p ?l))
    )
  )

  (:action drive
    :parameters (?r - robot ?from ?to - location)
    :precondition (and
      (at ?r ?from)
      (road ?from ?to)
      (>= (fuel ?r) (fuel-required ?from ?to))
    )
    :effect (and
      (not (at ?r ?from))
      (at ?r ?to)
      (decrease (fuel ?r) (fuel-required ?from ?to))
    )
  )

  (:action refuel
    :parameters (?r - robot ?l - location)
    :precondition (and
      (at ?r ?l)
      (gas-station ?l)
    )
    :effect (and
      (increase (fuel ?r) (refuel-amount ?l))
    )
  )

  (:action deliver
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and
      (at ?r ?l)
      (carrying ?r ?p)
      (delivery-destination ?p ?l)
    )
    :effect (and
      (delivered ?p)
      (not (carrying ?r ?p))
    )
  )
)
