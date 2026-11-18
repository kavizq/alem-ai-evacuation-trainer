# Alem AI Evacuation Trainer

A four-floor local 3D training application for the AI Fundamentals project. Practise choosing an evacuation route when an elevator is unavailable and a sensor report is uncertain. ADEKA combines collision-aware A* search, Bayesian inference and MDP value iteration. The environment and sensor assumptions are fictional.

## Quick start

The separate Windows portable ZIP in the submission opens with `AlemAITrainer.exe` and includes its runtime. Extract the entire folder and keep `_internal` beside the executable. The source setup below is for running or editing the Python project.

Install Python 3.10 or newer. On Windows, double-click `START_WINDOWS.cmd`. On macOS or Linux, run `sh start_macos_linux.sh`. The first launch downloads Panda3D into an isolated `.venv`; later launches work offline. Allow a short initial loading period for the original 3D models.

Alternatively:

```sh
python -m pip install -r requirements.txt
python main.py
```

Run from a graphical desktop. The application needs an OpenGL-capable display. The updated version has been exercised on Windows with Python 3.12 and Panda3D 1.10.16. The cross-platform launch scripts are supplied, but the revised game has not been run on macOS or Linux in this session.

## Play

Press Space to leave the opening lecture. Move with WASD and look with the mouse or arrows. Find the cyan route terminal, press E, then press 1 to accept ADEKA's route or 2 to choose the other available exit. Press 3 inside the panel to inspect the AI calculations. Q closes the panel.

Follow the cyan line on the floor and the actual floor plan at the upper right. Press E near the selected stair entrance. Repeat on the next floor. On floor 1, the exits lead to the plaza, the original closing cards and the dedication to Dilnura Ali. Press Enter after completion to view the training results.

Original recorded ADEKA lines play through Panda3D on Windows as well as other platforms. New messages use an installed offline system voice where available (English Zira is preferred on Windows). M mutes speech and game sound. Original recordings and the wording of all three closing cards are preserved; new system speech may use a different voice.

- E also reads the two optional amber information stations.
- U recalculates the route from the current position. In the smoke scenario on floor 2, the first U after route selection closes that planned exit and demonstrates replanning.
- F5 cycles the three scenarios and starts a fresh exercise.
- C restores a training checkpoint. R starts the current scenario again.
- H gives guidance. Escape releases the mouse; clicking the game captures it again. Shift increases movement speed.

Routes are recommendations. Incorrect choices never lock every exit. An unavailable exit remains visibly marked and cannot be used. Students follow the selected exit. Results count the player's actions; NPC positions do not determine completion.

## Scenarios

```sh
python main.py --scenario clear
python main.py --scenario smoke
python main.py --scenario blocked
python main.py --legacy
```

`clear` supplies NO ALERT on all floors. `smoke` supplies ALERT except on floor 3 and supports the live floor-2 closure. `blocked` removes the initially shortest exit. These are deterministic scenarios for reproducible classroom demonstrations. A repeated scan uses the same current observation, rather than treating the same reading as independent new evidence.

`--legacy` preserves Adilzhan's original quiz campaign. Its educational 6x6 grid and three-error lockdown belong only to that original mode. The new default trainer uses actual movement collisions and has no error lockdown.

## Implementation

`navigation.py` implements four-neighbour A* at 0.5 m spacing using the same `can_walk` predicate as player movement. It finds candidate routes to the two real game gates. `training_core.py` updates a 20% blockage prior using an 80% sensitivity and a 20% false-alarm rate. Its finite discounted MDP compares routes using their measured lengths, modeled walking speed and a blocked-attempt penalty. `training.py` connects the decision to floor guidance, student destinations and metrics.

The MDP has a junction, an approach state per available exit and a terminal exit state. A suspect approach succeeds or returns to the junction with a penalty. Synchronous value iteration solves the Bellman equation with discount 0.98. This is planning with a supplied transition model, not reinforcement learning from collected data. The older `ai_core.py` remains for legacy compatibility.

## Verification

```sh
python -m unittest discover -s tests -v
python verify_training.py
```

The integration check opens an offscreen graphics buffer and drives the real movement loop through all four floors in all three scenarios. It checks collision-safe paths, the live closure, checkpoint restoration, invalid-save handling and the final summary. It writes screenshots and `verification/training_checks.json`. Graphical checks require an available rendering driver even when the window is offscreen.

`user_data/training_save.json` stores an active checkpoint. `user_data/last_result.json` stores the most recent completed exercise. These local files and personal runtime logs are excluded from Git.

## Submission materials

- `docs/TECHNICAL_REPORT.md` and its PDF reading version
- `docs/AI_USAGE_DECLARATION.md`
- `docs/TEAM_CONTRIBUTIONS.md`
- `docs/DEFENSE_RU.md`
- `docs/DEMO_SCRIPT.md`
- A six-slide presentation and a captioned demo video in the delivered submission bundle

## Scope and ownership

Adilzhan created the supplied baseline project, according to Amir. Amir initiated and directed this revision. Codex provided substantial implementation, testing and writing assistance; see the declaration. The original external model attribution is preserved in `assets/seated-source.txt`. No new blanket license is asserted over the inherited assets. This is a classroom prototype, without a surveyed Alem AI floor plan, real sensor calibration, smoke physics, crowd validation or measured learning outcomes.
