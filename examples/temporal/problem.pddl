(define (problem deliver-package)
  (:domain temporal-logistics)

  (:objects
    truck1 - truck
    package1 - package
    depot destination - location
  )

  (:init
    (at package1 depot)
    (truck-at truck1 depot)
    (road depot destination)
  )

  (:goal
    (at package1 destination)
  )
)