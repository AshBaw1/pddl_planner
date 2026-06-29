(define (problem robot-costs-problem)
  (:domain robot-costs)

  (:objects
    a b c d - location
  )

  (:init
    (at a)

    (connected a b)
    (connected b d)
    (connected a c)
    (connected c d)
    (connected a d)

    (= (move-cost a b) 2)
    (= (move-cost b d) 2)
    (= (move-cost a c) 5)
    (= (move-cost c d) 1)
    (= (move-cost a d) 10)

    (= (total-cost) 0)
  )

  (:goal
    (at d)
  )

  (:metric minimize (total-cost))
)