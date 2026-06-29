(define (domain temporal-logistics)
  (:requirements :typing :durative-actions)
  
  (:types truck package location)

  (:predicates
    (at ?p - package ?l - location)
    (truck-at ?t - truck ?l - location)
    (in ?p - package ?t - truck)
    (road ?from ?to - location)
  )

  (:durative-action load
    :parameters (?p - package ?t - truck ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (at ?p ?l))
      (at start (truck-at ?t ?l))
      (over all (truck-at ?t ?l))
    )
    :effect (and
      (at start (not (at ?p ?l)))
      (at end (in ?p ?t))
    )
  )

  (:durative-action drive
    :parameters (?t - truck ?from ?to - location)
    :duration (= ?duration 20)
    :condition (and
      (at start (truck-at ?t ?from))
      (at start (road ?from ?to))
    )
    :effect (and
      (at start (not (truck-at ?t ?from)))
      (at end (truck-at ?t ?to))
    )
  )

  (:durative-action unload
    :parameters (?p - package ?t - truck ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (in ?p ?t))
      (at start (truck-at ?t ?l))
      (over all (truck-at ?t ?l))
    )
    :effect (and
      (at start (not (in ?p ?t)))
      (at end (at ?p ?l))
    )
  )
)