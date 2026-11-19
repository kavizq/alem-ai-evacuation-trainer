# Alem AI Evacuation Trainer

Technical report for AI Fundamentals  
Team members: Amir and Adilzhan  
Revision date: 19 November 2026

## Abstract

Our project is a local four-floor 3D application for practising route choices in a fictional Alem AI setting, where an exercise alarm makes elevators unavailable. The player compares stair routes with ADEKA, which connects A* search over walkable geometry, Bayesian inference from a noisy sensor, and MDP value iteration. These calculations determine the recommended exit and visible guide, while three repeatable scenarios show how a changing condition affects the plan. Evaluation covers algorithm calculations and complete scenario traversal, with learning outcomes left for future study.

## Problem and objectives

Evacuation preparation involves choosing an alternative when a familiar route is unavailable and interpreting uncertain warnings, which makes route selection a useful subject for repeatable, interactive exercises in a virtual building. It targets students and instructors who need a classroom demonstration and a way to discuss decision consequences without staging a physical incident.

The implementation objectives are to calculate routes around actual game obstacles, represent uncertainty explicitly, compare sequential consequences, respond to a newly unavailable exit, and give a reviewable session summary. A four-floor route and an explanatory AI panel make the application demonstrable within the course defense, using a fictional layout inspired by Alem AI rather than a surveyed reconstruction.

## Original game and revision

Adilzhan developed the original game, which supplies the building, lecture sequence, movement, characters and stairs, together with an educational 6x6 grid, Bayes' rule and a one-step expected-reward decision. Its campaign mainly requires answering questions at terminals, with three incorrect answers leading to an all-exits lockdown.

The new default mode retains the original environment and adds practical route decisions, a map derived from collision geometry, multistep value iteration, three scenarios, a live exit update, local session metrics and separate training checkpoints. Optional amber stations provide context, and the player can choose an alternative without triggering an all-exits punishment, while the original quiz campaign remains available with --legacy. Platform path conversion and guarded offscreen input access address launch issues discovered during verification on Windows.

## Architecture and data flow

The application uses Python and Panda3D 1.10.16, with campaign.py providing the inherited 3D environment and training.py connecting the exercise state to route guidance, menus, student destinations and metrics. navigation.py provides collision-aware A*, while training_core.py contains Bayes integration, finite-MDP construction, value iteration and session serialization, and ai_core.py retains the calculations used by the legacy campaign.

At a route terminal, A* computes a path to each reachable exit, with the initially shorter approach becoming the scenario's suspect approach, while Bayes transforms the current sensor report into a blockage probability. The MDP receives the candidate path lengths, that posterior and the unavailable-exit set, and its policy selects an exit. The application displays that exit's already calculated A* route and uses the same destination for the moving student characters. Replanning runs the pipeline again from the current position.

All gameplay calculations run locally, with installation downloading the pinned game engine and subsequent runs requiring no language-model service. Scenario parameters are educational inputs, rather than measured observations from a building.

## Topic one A star search

The search uses a four-neighbour lattice with 0.5 m spacing in the same world coordinates as the player. The successor predicate is can_walk, which accounts for the circular perimeter, room obstacles, atrium opening, fixtures and the exercise's unavailable gate barrier. Each move costs one lattice step, and the queue priority is f(n) = g(n) + h(n), using Manhattan distance to the chosen gate as the heuristic. The returned route includes the initial and destination lattice points, with the displayed distance obtained by summing consecutive segments in metres.

The application searches independently toward the candidate gate approaches, separating geometric reachability from the decision about uncertainty. A* gives a shortest path on its discrete collision model, not an assurance that a physical real-world route is safe. Four-direction motion and lattice sampling approximate the continuous 3D environment. Integration checks also move the actual player along the calculated paths to detect disagreement between the lattice and movement collisions.

With a heap and a finite explored grid, the conventional worst-case graph-search cost is O((V+E) log V), with O(V) stored state and at most four neighbours per lattice node. The map shown to the player samples that same movement predicate rather than the inherited unrelated 6x6 puzzle grid. [1]

## Topic two Bayesian inference

The assumed blockage prior is 0.20, with sensor sensitivity P(ALERT given blocked) set to 0.80 and the false-alarm rate P(ALERT given clear) set to 0.20, giving the following Bayesian posteriors:

P(blocked given ALERT) = (0.80 x 0.20) / ((0.80 x 0.20) + (0.20 x 0.80)) = 0.50.

P(blocked given NO ALERT) = (0.20 x 0.20) / ((0.20 x 0.20) + (0.80 x 0.80)) = 1/17, approximately 0.0588.

An alert raises the blockage belief to 50%, while the absence of an alert leaves a smaller residual uncertainty of about 5.88%. The implementation validates probability ranges and rejects zero-probability observations. Re-reading the current report does not accumulate it as independent evidence, and the posterior supplies the suspect approach's MDP transition probabilities. These values describe the supplied scenario model, not actual calibrated smoke detectors. [2]

## Topic three Sequential decisions with value iteration

The finite MDP contains JUNCTION, APPROACH_LEFT and/or APPROACH_RIGHT, and the terminal state EXIT. An unavailable route has no junction action, while choosing an exit moves deterministically to its approach and incurs 70% of that route's modeled travel-time cost. At an approach, CONTINUE succeeds with probability 1-p or returns to JUNCTION with probability p. The remaining 30% of travel-time cost applies in either outcome, with a blocked attempt adding a 90-unit penalty. Only the suspect approach uses the Bayesian posterior. Other approaches have zero blockage probability within this deliberately restricted model.

The model uses a walking speed of 2.7 m/s, with the algorithm maximizing expected discounted return at gamma = 0.98. Every synchronous sweep computes V_next(s) = max_a sum_s' T(s,a,s') [R(s,a,s') + gamma V(s')]. It stops when the maximum value change is below 1e-9, or raises an error at its iteration limit. It then derives greedy actions and a Bellman residual, with EXIT assigned value zero. [3]

This extends the original single expected-reward comparison with a sequential state model, planning with supplied rewards and transitions rather than learning them from player data. The recovery transition uses a fixed belief and a modeled penalty. It does not simulate changing smoke, infer a new belief after an attempted passage, or implement a complete POMDP. Those are explicit simplifications.

## Scenarios and interaction

The clear scenario supplies NO ALERT on every floor, while smoke supplies ALERT except on floor 3. Its floor-2 update closes the player's selected exit and recomputes a route when U is pressed. The blocked scenario removes the initially shortest exit. The scenarios are deterministic, supporting repeatable demonstrations and comparisons.

The player may read either amber station, open the cyan terminal, inspect the AI explanation, choose an exit and follow the route. Stairs remain available unless a scenario closes one; feedback never locks every exit. Completion follows the player's progression, with student following serving as a visual guide. Narration uses local F5-TTS audio generated from Amir's approved voice reference. Dynamic route speech points to the displayed numerical values. The speech model is not a runtime dependency, and all original closing cards retain their wording, including the Dilnura Ali dedication, with Enter opening the results.

## Evaluation method and observed results

The verification environment was Windows with Python 3.12.14 and Panda3D 1.10.16. The revised test suite includes 28 unit tests, covering original calculations, legacy compatibility, camera handling, navigation, Bayesian values, signal-sensitive actions, closed routes, malformed MDPs, checkpoint data, a known-answer value-iteration problem, consistent narration and door use without visiting the terminal. All 24 combinations of three scenarios, four floors and two doors were exercised without visiting the terminal; no exceptions occurred.

A separate Windows 64-bit portable build includes the runtime and opens without a Python installation. Its packaged resource and route check completed on all four floors with exit code zero. The preserved original quiz campaign also passed its success, failure and checkpoint checks.

verify_training.py uses a real offscreen rendering buffer and the ordinary movement loop. It traverses all four floors in all three scenarios, checks path points against collisions, exercises the explanation panel, triggers the live closure, restores a checkpoint including that closure, rejects an invalid checkpoint without changing the active run, and reaches the final results. All three scenario traversals passed. Records appear in verification/training_checks.json. Rendered screens were inspected separately. The checks assess functionality, while learning outcomes remain unmeasured.

At the floor-4 terminal in the smoke scenario, the measured candidate paths were LEFT 25 m and RIGHT 27 m. The shortest-only baseline chose LEFT, while the MDP chose RIGHT at a blockage posterior of 0.50. Four Bellman sweeps gave a residual below 1e-8. The nominal extra route distance was 2 m, approximately 0.74 seconds at the model speed, in exchange for avoiding the modeled uncertain approach.

The smoke scenario on floor 3 used posterior 0.0588 and still selected RIGHT for paths of 25 m and 27 m. This is consistent with the specified penalty: lower risk does not necessarily reverse a policy when the detour is short. A separate unit case with 20 m and 40 m alternatives verifies that changing only ALERT to NO ALERT can reverse the selected action. After the floor-2 live update, only LEFT remained available and the MDP selected it despite its modeled uncertainty. That case required 69 sweeps, illustrating a constrained choice where the available route still carries modeled uncertainty.

The results screen records time, walked distance, route changes, entries into the sensor-marked zone and exits used without the selected guidance. It also compares summed modeled route risks for the last decision per floor with the shortest-only alternative at those same decision points. These sums are comparative scenario scores, without a direct interpretation as incident probabilities or measured improvements in evacuation safety.

## Limitations and next validation

The building geometry, blockage prior, sensor calibration and penalties are synthetic, while the model omits smoke propagation, fire dynamics, physical crowd congestion, accessibility needs, communications failures and real building regulations. Character following provides a visual aid, with A* discretizing collision geometry and value iteration operating on a small abstract route model. The revised application has been exercised on Windows; fresh macOS and Linux runs remain to be checked.

A next study could ask consenting participants to complete matched scenarios before and after training, compare route-choice errors and completion time, and gather usability feedback. Building-specific operational use would require actual architectural plans and professional review of the scenarios and assumptions.

## Submission and reproducibility

The submission includes source code and launch scripts, a Windows portable application, a seven-slide presentation, a demo video, an AI Usage Declaration and a Team Contribution Statement. The repository is https://github.com/kavizq/alem-ai-evacuation-trainer, with local launch and verification commands in README.md. Adilzhan's original game forms the project foundation, while the declaration describes the tools used during the later extension.

## References

[1] David Poole and Alan Mackworth. Artificial Intelligence Foundations of Computational Agents, second edition, section 3.6.1 A* Search. https://artint.info/2e/html2e/ArtInt2e.Ch3.S6.SS1.html

[2] David Poole and Alan Mackworth. Artificial Intelligence Foundations of Computational Agents, second edition, section 8.1.3 Conditional Probability. https://artint.info/2e/html2e/ArtInt2e.Ch8.S1.SS3.html

[3] University of California Berkeley. CS 188 Project 3, Value Iteration. https://inst.eecs.berkeley.edu/~cs188/fa26/projects/proj3/

