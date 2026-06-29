(define (problem robot-navigation-problem)
  (:domain robot-navigation)

  (:objects
    r1 - robot
    a b c d - location
  )

  (:init
    (at r1 a)
    (connected a b)
    (connected b c)
    (connected c d)
  )

  (:goal (and
    (at r1 d)
  ))
)
