# Game demonstration

## What the demo shows

The demonstration follows one exercise from the opening classroom to the plaza, starting with a terminal comparison and showing how the recommendation becomes a visible route. The floor-2 closure provides the main change of conditions, followed by a new route and the final statistics.

The repository's captioned video uses actual application renders with scripted movement, lasting about two and a half minutes. Its recording script can pause or speed up playback while the captions explain the calculations.

## Live demo, 3 to 5 minutes

1. Launch `python main.py --scenario smoke`, press **Space** and show the starting floor, where the exercise reports possible smoke and unavailable elevators.
2. Open the cyan terminal with **E**, compare the two route lengths and sensor posterior, then press **3** to show how the algorithms connect.
3. Press **1** and follow the cyan guide, pointing out the matching route on the map before using the stairs with **E**.
4. On floor 3, the sensor gives NO ALERT and the posterior falls, although a small detour can still be preferable under the model's blocked-attempt penalty.
5. On floor 2, choose a route and press **U**, which closes the selected exit in this scenario and triggers a replacement recommendation.
6. Continue to the plaza, show the original ending and press **Enter** for the results, covering time, distance, route changes and model scores.

A checkpoint from an earlier run can shorten the demonstration, with the restored section introduced as saved progress. The risk total compares modelled choices at the same decision points, while the completion statistics describe the player's run.

## Defense timing

The planned order is 2 minutes for the problem and objectives, 3 to 5 minutes for gameplay, 2 minutes for the AI topics and up to 3 minutes for questions. The algorithm explanation follows the same route as the game calculation, starting with A*, continuing through the Bayesian update and finishing with the MDP decision.
