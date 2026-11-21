# Alem AI Evacuation Trainer

A local 3D game for practising evacuation route choices, built for the AI Fundamentals course. ADEKA combines A* search, Bayesian inference and MDP planning to recommend an exit, show its route and explain the decision.

> Короче, ты на четвёртом этаже, срабатывает учебная тревога, а лифты недоступны. Нужно выбрать лестницу и вывести группу, ADEKA помогает сравнить пути и показывает, куда идти. Если выбранный выход закрывается, маршрут можно пересчитать, а в терминале посмотреть, как получилась рекомендация.

## Running the game

For the Windows build, extract `AlemAI_Windows.zip` and open `AlemAITrainer.exe`. Python and Panda3D are included, and the `_internal` folder stays beside the application. A desktop shortcut can point directly to that EXE, so the game is one double-click away.

To run from source, install Python 3.10 or newer and open `START_WINDOWS.cmd` on Windows, or run the following command from the project folder on macOS or Linux:

```sh
sh start_macos_linux.sh
```

The launcher creates a local `.venv` and installs Panda3D on the first run, after which the game works offline. You can also launch it directly:

```sh
python -m pip install -r requirements.txt
python main.py
```

The revised game has been tested on Windows with Python 3.12 and Panda3D 1.10.16, while the macOS and Linux launchers are provided without a confirmed run on those systems. A graphical desktop with an OpenGL-capable display is required.

## Playing a round

Press **Space** to finish the opening scene, then use **WASD** to move and the mouse or arrow keys to look around. At the cyan terminal, **E** opens the route comparison, **1** accepts ADEKA's recommendation, **2** selects another available exit, and **3** explains the calculations. **Q** closes the panel.

Once you choose an exit, a cyan line appears on the floor and the map shows its route. Follow it to the stairs and press **E**, repeating the process on each floor until you reach the plaza. The original closing cards and dedication remain at the end, followed by the training results when you press **Enter**.

| Key | Action |
|---|---|
| E | Inspect a terminal or information station, or use nearby stairs |
| 1 / 2 | Accept the recommendation or choose the other available exit |
| 3 | Show the AI explanation inside the terminal |
| U | Recalculate the route from the current position |
| F5 | Switch scenario and start a fresh exercise |
| C | Restore the saved training checkpoint |
| R | Restart the current scenario |
| H | Show a hint |
| M | Mute or unmute narration and game sound |
| Escape | Release the mouse, then click the game to capture it again |
| Shift | Move faster |

## Where the AI helps

The route terminal is where the three topics meet, A* finds paths around the level's obstacles, Bayes updates a blockage belief from the sensor reading, and the MDP compares the possible consequences before recommending an exit. Choosing the recommendation turns that result into the cyan floor guide.

For example, the recorded floor-4 smoke case has a 25 m left route and a 27 m right route. The model assigns the suspect left approach a 50% blockage probability after an alert, so the policy recommends the slightly longer right route. Route lengths can change with the player's position.

For the clearest replanning example, use the `smoke` scenario, choose a route on floor 2 and press **U**. The exercise closes that selected exit and ADEKA calculates a new route to an available one. On other floors, **U** updates the recommendation from your current position.

## Scenarios

```sh
python main.py --scenario clear
python main.py --scenario smoke
python main.py --scenario blocked
python main.py --legacy
```

`clear` gives NO ALERT on every floor, `smoke` gives ALERT except on floor 3 and includes the floor-2 closure, while `blocked` removes the initially shortest exit. The scenarios use fixed inputs so a demonstration can be repeated, and reopening the same sensor reading does not count as new independent evidence.

The default trainer lets the player choose a route without a quiz, while `--legacy` opens Adilzhan's original campaign with terminal questions, its 6x6 activity grid and three-error lockdown. Terminals remain optional in the trainer, with unguided exits recorded in the results. A closed exit stays unavailable, and character following provides a visual guide while player progression determines completion.

## How the algorithms connect

`navigation.py` runs four-neighbour A* on a 0.5 m grid, using the same `can_walk` checks as player movement. It returns candidate paths and their lengths, which `training_core.py` combines with the Bayesian update from `ai_core.py`.

The sensor model uses a 20% blockage prior, 80% sensitivity and a 20% false-alarm rate. Those assumptions give a 50% posterior after ALERT and about 5.88% after NO ALERT, supplying the uncertain approach's transition probabilities.

The MDP represents a junction, an approach to each available exit and a terminal exit state. A blocked attempt can return to the junction with a 90-unit penalty, and value iteration evaluates the resulting sequence with a 0.98 discount. The model plans with supplied probabilities rather than learning them from player experience, while `training.py` connects the selected action to the map, floor guide, characters and session results.

## Sound and saves

Narration plays from local audio files generated with F5-TTS using Amir's selected voice reference, so the game does not load a speech model or contact an online service. Route speech names the selected side and refers to the distance and risk displayed on screen, while an unknown cue remains subtitled. Model and voice attribution are in [audio/adeka_f5/CREDITS.txt](audio/adeka_f5/CREDITS.txt).

The current checkpoint is stored in `user_data/training_save.json`, and the latest completed exercise appears in `user_data/last_result.json`. Personal saves and runtime logs stay outside Git.

## Checks and project notes

```sh
python check.py
python check.py --full
```

The integration check drives the regular movement loop through four floors in each scenario, checking collisions, exit closure, explanations, checkpoint restoration and the final summary. It writes screenshots and `verification/training_checks.json`, using a graphics driver even when rendering offscreen. The latest recorded gameplay checks include 28 unit tests and 24 door-without-terminal cases, with details in [verification/VALIDATION.md](verification/VALIDATION.md).

The environment and sensor parameters are fictional, and the prototype has no measured learning effect, smoke propagation or validated crowd simulation. Its results describe decisions within the exercise, with summed risk scores serving as model comparisons rather than incident probabilities.

## Documents

- [Technical report](docs/TECHNICAL_REPORT.md), with its [PDF version](docs/TECHNICAL_REPORT.pdf)
- [AI Usage Declaration](docs/AI_USAGE_DECLARATION.md)
- [Team Contribution Statement](docs/TEAM_CONTRIBUTIONS.md)
- [Seven-slide presentation](docs/PRESENTATION_SUBMISSION.pptx)
- [Demo script](docs/DEMO_SCRIPT.md) and [Russian defense notes](docs/DEFENSE_RU.md)
- [Quick start in Russian](START_HERE_RU.md)

Adilzhan developed the original game, and Amir directed its extension into an evacuation trainer. Tools used for the later revision are described in the AI Usage Declaration, while the inherited model attribution remains in [assets/seated-source.txt](assets/seated-source.txt).

## Project folders

The root contains the game modules and launchers, `checks/` holds the integration tools, and `tests/` contains the unit suite. Materials and explanations are in `docs/`, resources are in `assets/` and `audio/`, while generated builds and personal saves stay outside Git.

To build the Windows application from source, install PyInstaller and run:

```sh
python -m PyInstaller --distpath build/windows --workpath build/temp packaging/AlemAITrainer.spec
```

The executable will appear in `build/windows/AlemAITrainer/`, alongside its runtime folder.
