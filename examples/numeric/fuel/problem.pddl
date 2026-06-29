(define (problem deliver-with-limited-fuel)
  (:domain numeric-delivery)

  (:objects
    robot1 - robot
    package1 - package
    depot station customer - location
  )

  (:init
    (at robot1 depot)
    (package-at package1 depot)
    (delivery-destination package1 customer)

    (road depot station)
    (road station customer)

    (gas-station station)

    (= (fuel robot1) 40)

    (= (fuel-required depot station) 20)
    (= (fuel-required station customer) 30)

    (= (refuel-amount station) 40)

  )

  (:goal
    (delivered package1)
  )
)
