# Alem AI Evacuation Trainer

Technical report for AI Fundamentals  
Team members: Amir and Adilzhan  
Revision date: 18 November 2026

## Abstract

Alem AI Evacuation Trainer is a local four-floor 3D application for practising route choices under uncertain sensor information. A fictional smoke alert interrupts a classroom session, elevators are unavailable, and the player leads a group toward stairs and ground-floor exits. The revision integrates three AI topics: A* search over the movement collision geometry, Bayesian inference from a noisy sensor, and a finite Markov decision process solved by value iteration. The selected decision produces visible floor guidance and changes student destinations. Three deterministic scenarios support reproducible demonstrations. Automated checks validate the calculations and drive actual movement through all four floors in every scenario. The project demonstrates a training mechanism and a connected AI pipeline; a human learning benefit remains to be measured.

## Problem and objectives

Evacuation preparation includes choosing an alternative when a familiar route is unavailable and interpreting warnings that do not establish certainty. The project addresses that preparation through repeatable, interactive exercises in a virtual building. It targets students and instructors who need a classroom demonstration and a way to discuss decision consequences without staging a physical incident.

The implementation objectives are to calculate routes around actual game obstacles, represent uncertainty explicitly, compare sequential consequences, respond to a newly unavailable exit, and give a reviewable session summary. A four-floor route and an explanatory AI panel make the application demonstrable within the course defense. The supplied environment resembles Alem AI but is not a surveyed reconstruction.

## Baseline and revision

According to Amir, Adilzhan created the supplied baseline. It contains the building, lecture sequence, movement, characters, stairs, a fictional 6x6 educational grid, Bayes' rule and a one-step expected-reward decision. Its campaign mainly requires answering questions at terminals. Three wrong answers cause an all-exits lockdown.

The new default mode retains the original environment and adds practical route decisions, a map derived from collision geometry, multistep value iteration, three scenarios, a live exit update, local session metrics and separate training checkpoints. Optional amber stations provide context. A player can choose the alternative exit without triggering an artificial all-exits punishment. The original quiz campaign remains available with --legacy. Platform path conversion and guarded offscreen input access address launch issues discovered during verification on Windows.

## Architecture and data flow

The application uses Python and Panda3D 1.10.16. campaign.py provides the inherited 3D environment. training.py subclasses it and connects the exercise state to route guidance, menus, student destinations and metrics. navigation.py provides collision-aware A*. training_core.py contains engine-independent Bayes integration, finite-MDP construction, value iteration and session serialization. ai_core.py remains unchanged for the legacy campaign.

At a route terminal, A* computes a path to each reachable game exit. The shortest initial approach becomes the scenario's suspect approach. Bayes transforms the current sensor report into a blockage probability. The MDP receives candidate path lengths, that posterior and the unavailable-exit set. Its policy selects an exit. The application displays that exit's already calculated A* route and uses the same destination for the moving student characters. Replanning runs the pipeline again from the current position.

No network or language-model request occurs during gameplay. Installation downloads the pinned game engine; subsequent runs work locally. Scenario parameters are educational inputs, rather than measured observations from a building.

## Topic one A star search

The search uses a four-neighbour lattice with 0.5 m spacing in the same world coordinates as the player. The successor predicate is can_walk, which accounts for the circular perimeter, room obstacles, atrium opening, fixtures and the exercise's unavailable gate barrier. Each move costs one lattice step. The queue priority is f(n) = g(n) + h(n), with Manhattan distance to the chosen gate as the heuristic. The returned route includes the initial and destination lattice points. Reported distance sums consecutive segment lengths in metres.

The application searches independently toward the two candidate gate approaches. This separates geometric reachability from the decision about uncertainty. A* gives a shortest path on its discrete collision model, not an assurance that a physical real-world route is safe. Four-direction motion and lattice sampling approximate the continuous 3D environment. Integration checks also move the actual player along the calculated paths to detect disagreement between the lattice and movement collisions.

With a heap and a finite explored grid, the conventional worst-case graph-search cost is O((V+E) log V), with O(V) stored state. Here each lattice node has at most four neighbours. The map shown to the player samples that same movement predicate rather than the inherited unrelated 6x6 puzzle grid. [1]

## Topic two Bayesian inference

The assumed prior blockage probability is 0.20. Sensor sensitivity P(ALERT given blocked) is 0.80, and the false-alarm rate P(ALERT given clear) is 0.20. Bayes' rule gives:

P(blocked given ALERT) = (0.80 x 0.20) / ((0.80 x 0.20) + (0.20 x 0.80)) = 0.50.

P(blocked given NO ALERT) = (0.20 x 0.20) / ((0.20 x 0.20) + (0.80 x 0.80)) = 1/17, approximately 0.0588.

The observation therefore changes a belief about blockage. An alert does not prove blockage, and a negative report leaves residual uncertainty. The implementation validates probability ranges and rejects zero-probability observations. Re-reading the same current report does not accumulate it as independent evidence. The posterior feeds the suspect approach's MDP transition probabilities. These values describe the supplied scenario model, not actual calibrated smoke detectors. [2]

## Topic three Sequential decisions with value iteration

The finite MDP contains JUNCTION, APPROACH_LEFT and/or APPROACH_RIGHT, and the terminal state EXIT. An unavailable route has no junction action. Choosing an exit moves deterministically to its approach and incurs 70% of that route's modeled travel-time cost. At an approach, CONTINUE succeeds with probability 1-p or returns to JUNCTION with probability p. The remaining 30% of the travel-time cost applies in either outcome; a blocked attempt adds a 90-unit penalty. Only the suspect approach uses the Bayesian posterior. Other approaches have zero blockage probability within this deliberately restricted model.

Modeled walking speed is 2.7 m/s. The algorithm maximizes expected discounted return using gamma = 0.98. Every synchronous sweep computes V_next(s) = max_a sum_s' T(s,a,s') [R(s,a,s') + gamma V(s')]. It stops when the maximum value change is below 1e-9, or raises an error at its iteration limit. It then derives greedy actions and a Bellman residual. EXIT has value zero. [3]

This replaces the baseline's single expected-reward comparison with a genuinely sequential state model. It is model-based planning; it does not learn rewards or transitions from player data. The recovery transition uses a fixed belief and a modeled penalty. It does not simulate changing smoke, infer a new belief after an attempted passage, or implement a complete POMDP. Those are explicit simplifications.

## Scenarios and interaction

The clear scenario supplies NO ALERT on every floor. The smoke scenario supplies ALERT except on floor 3. Its floor-2 update closes the player's selected exit and recomputes a route when U is pressed. The blocked scenario removes the initially shortest exit. The scenarios are deterministic so both students can reproduce the same defense.

The player may read either amber station, open the cyan terminal, inspect the AI explanation, choose an exit and follow the route. Stairs remain available unless a scenario closes one; feedback never locks every exit. Completion follows player progression, not physical arrival of every NPC. Narration uses local F5-TTS audio generated from Amir's approved voice reference. Dynamic route speech points to the displayed numerical values. The speech model is not a runtime dependency. All original closing cards, including the Dilnura Ali dedication, retain their wording. Enter opens the results.

## Evaluation method and observed results

The verification environment was Windows with Python 3.12.14 and Panda3D 1.10.16. The revised test suite includes 28 unit tests, covering original calculations, legacy compatibility, camera handling, navigation, Bayesian values, signal-sensitive actions, closed routes, malformed MDPs, checkpoint data, a known-answer value-iteration problem, consistent narration and door use without visiting the terminal. All 24 combinations of three scenarios, four floors and two doors were exercised without visiting the terminal; no exceptions occurred.

A separate Windows 64-bit portable build includes the runtime and opens without a Python installation. Its packaged resource and route check completed on all four floors with exit code zero. The preserved original quiz campaign also passed its success, failure and checkpoint checks.

verify_training.py uses a real offscreen rendering buffer and the ordinary movement loop. It traverses all four floors in all three scenarios, checks path points against collisions, exercises the explanation panel, triggers the live closure, restores a checkpoint including that closure, rejects an invalid checkpoint without changing the active run, and reaches the final results. All three scenario traversals passed. Records appear in verification/training_checks.json. Rendered screens were inspected separately. These are automated integration results, not a participant study.

At the floor-4 terminal in the smoke scenario, the measured candidate paths were LEFT 25 m and RIGHT 27 m. The shortest-only baseline chose LEFT. With posterior 0.50, the MDP chose RIGHT. Four Bellman sweeps gave a residual below 1e-8. The nominal extra route distance was 2 m, approximately 0.74 seconds at the model speed, in exchange for avoiding the modeled uncertain approach.

The smoke scenario on floor 3 used posterior 0.0588 and still selected RIGHT for paths of 25 m and 27 m. This is consistent with the specified penalty: lower risk does not necessarily reverse a policy when the detour is short. A separate unit case with 20 m and 40 m alternatives verifies that changing only ALERT to NO ALERT can reverse the selected action. After the floor-2 live update, only LEFT remained available and the MDP selected it despite its modeled uncertainty. That case required 69 sweeps and illustrates a constrained choice rather than a guarantee of a risk-free option.

The results screen records time, walked distance, route changes, entries into the sensor-marked zone and exits used without the selected guidance. It also compares summed modeled route risks for the last decision per floor with the shortest-only alternative at those same decision points. These sums are scenario scores, not the probability of an incident and not a causal estimate of training effectiveness. They should not be reported as real-world lives saved or measured improvement in evacuation safety.

## Limitations and next validation

The building geometry, blockage prior, sensor calibration and reward penalties are synthetic. The model omits smoke propagation, fire dynamics, physical crowd congestion, accessibility needs, communications failures and real building regulations. Character following is a visual aid. A* discretizes collision geometry, and value iteration operates on a small abstract route model. The revised application has been exercised on Windows; fresh macOS and Linux runs remain to be checked.

A next study could ask consenting participants to complete matched scenarios before and after training, compare route-choice errors and completion time, and gather usability feedback. An instructor should verify topic coverage and review the rewards and scenarios. Actual architectural plans and professional emergency review would be needed before making any building-specific operational claim.

## Submission and reproducibility

The bundle includes source and launch scripts, a six-slide presentation, a two-to-three-minute demonstration video, an AI-use declaration, a contribution statement and Russian defense notes. The repository belongs to Amir's authenticated GitHub account kavizq. AI assistance is disclosed: Codex generated substantial revision code and draft materials and executed automated checks. Amir and Adilzhan should independently review and rehearse the final version and complete the signature sections before assessment.

## References

[1] David Poole and Alan Mackworth. Artificial Intelligence Foundations of Computational Agents, second edition, section 3.6.1 A* Search. https://artint.info/2e/html2e/ArtInt2e.Ch3.S6.SS1.html

[2] David Poole and Alan Mackworth. Artificial Intelligence Foundations of Computational Agents, second edition, section 8.1.3 Conditional Probability. https://artint.info/2e/html2e/ArtInt2e.Ch8.S1.SS3.html

[3] University of California Berkeley. CS 188 Project 3, Value Iteration. https://inst.eecs.berkeley.edu/~cs188/fa26/projects/proj3/

Implementation evidence: training_core.py, navigation.py, training.py, tests/test_training_core.py and verification/training_checks.json. The supplied asset source is retained in assets/seated-source.txt.
