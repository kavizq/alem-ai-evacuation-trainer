# Demo video and live demonstration

## Video

The delivered video uses actual renders from the application, scripted playback and explanatory captions. It is an automated demonstration, rather than a recording of a student manually completing the exercise. Runtime duration is approximately two and a half minutes. Recorded playback may pause or accelerate movement to keep the algorithm explanation readable.

Sequence: training problem and opening classroom; floor-4 route comparison; Bayes and MDP explanations; follow a collision-aware cyan route; floor-2 planned-exit closure and replanning; descend to the plaza; show the metrics summary and prototype limitations.

## Live demo lasting 3 to 5 minutes

1. Launch `python main.py --scenario smoke` and press Space. Explain the fictional smoke alert and unavailable elevators.
2. Walk to the cyan terminal. Press E, read the posterior and both route lengths, and press 3 to reveal value iteration and expected returns.
3. Press 1 and follow the cyan guide. Show that the mini-map matches the walkable geometry. Press E near the chosen stairs.
4. On floor 3, point out NO ALERT and the lower posterior. Explain that a lower probability need not change the preferred exit when route lengths are similar.
5. On floor 2, select the route and press U. Show that the selected exit becomes unavailable, disappears from the available actions and receives a replacement route.
6. Reach floor 1 and the plaza. Explain time, distance, sensor-zone entries and modeled risk. A summed risk score is not an overall probability of harm.

For a shorter defense, demonstrate the first route and the floor-2 update using a rehearsed checkpoint created during your own run. Avoid presenting a restored checkpoint as a complete live traversal.

## Timing

Problem and objectives: 2 minutes. Live demo: 3 to 5 minutes. Explanation of search, probability and sequential decision making: 2 minutes. Questions: up to 3 minutes. Rehearse with the exact classroom computer and both students answering individually.
