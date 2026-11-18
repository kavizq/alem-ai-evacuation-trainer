# Alem.ai-inspired educational game

A fictional four-floor Python/Panda3D game featuring ADEKA. The layout, emergency, sensor values and security rules are invented classroom material. No new game or character name has been assigned.

## Run on this Mac

```sh
cd /Users/adilzhan/Downloads/alem_ai_escape_3d
.venv/bin/python main.py
```

The desktop window needs access to the macOS graphical session. A sandboxed launch may abort in Cocoa. The existing environment includes Panda3D. The original requirements file is retained. For a fresh environment, install `panda3d==1.10.16`.

## Controls

- The opening starts from a seat in Qairu, turns to show the 50 seated students, then flies across the hall. WASD or Space skips straight to the evacuation. Russian Ц/Ф/Ы/В also work. Mouse or arrow keys look around.
- E reads a nearby amber evidence station, opens the cyan terminal, or enters a green stair gate.
- 1–3 submits the displayed answer. Three incorrect submissions lock all exits.
- H gives a conceptual ADEKA hint. Q closes the question.
- Space skips the opening lecture. Escape toggles mouse capture. Click the game window if it does not have keyboard focus.
- C restores the checkpoint. R begins a new run including the lecture.
- M toggles sound and English speech. Close the window to quit.

On every floor, inspect both amber stations, solve the terminal, then walk to either green gate and press E. The map marks your current cell in white and evidence stations in amber. The final decision highlights the computed detour and the excluded corridor. Floor 4 teaches A*, floor 3 Bayes, floor 2 one-step expected utility, and floor 1 combines them. Checkpoints record floor, evidence, decisions and accumulated errors. Completed runs require R to replay.

English ADEKA speech uses the macOS Samantha voice through `say`. Subtitles remain available. Ambient audio, alarm and footsteps are local generated WAV files. The four playable floors sit 4.2 metres apart in the shared exterior scene. Graphics use textured floors with baked daylight and shadows, acoustic ceilings, glazed meeting rooms and server rooms, modeled furniture, animated students, glass partitions, a domed atrium, six students with individual clothing and an exterior inspired by the Nur Alem sphere and its EXPO plaza with fixed-function rendering. One active floor is loaded at a time.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q main.py campaign.py verify_campaign.py verify_walk.py
.venv/bin/python verify_campaign.py
.venv/bin/python verify_walk.py
.venv/bin/python verify_runtime.py
.venv/bin/python verify_playthrough.py
```

The four verification scripts create real graphical windows and use isolated temporary saves. They verify floor progression, both outcomes, checkpoint restoration and collision-safe routes. Screenshots are written to `verification/`. These checks automate interactions and do not establish a human completion time. The design target is 8–12 minutes including exploration, reading and problem solving.

`main_before_campaign.py` preserves the previous entrypoint and provides the original Panda3D movement/HUD foundation. All earlier backups remain. `ai_core.py` and the console demo remain intact. `README_before_campaign.md` preserves the previous instructions.

## Circular-interior revision (12 November 2026)

Backup: `backup-before-rotunda.89LH5n`. Circular halls are 49 m across, with curved glass, shallow vaults, radial beams, quiet booths, white planters and office chairs. These are a fictional adaptation of supplied photos, not an architectural reconstruction. References: https://lenz.kz/office-for-akas-development-almaty-copy/ and https://www.idc-corporation.com/projects/alem-ai . No surveyed floor plan was located.

Both stair flights now have enclosed cores, floor openings and a six-second camera descent. A brief fade connects the landing to the next playable floor. Students have articulated elbows, fingers, revised faces, hair and fabric surfaces; these remain procedural models, not scanned photorealistic assets.

WASD speed starts at 2.7 m/s. Each completed floor adds 10% of base speed; solving the current terminal adds 25% of base speed. Shift multiplies the resulting speed by 1.45. The upper guidance shows the next objective, straight-line distance and bearing. The map is the educational task grid, not the entire circular floor plan: S=start, @=player cell, 1/2=evidence, T=terminal, E=exits.

Verified on macOS: eight unit tests; movement and keyboard camera; opening lecture with 50 students; normal-movement four-floor playthrough; success and failure endings; checkpoint restoration; both stair gates and transition fade; speed multipliers. Graphical checks use isolated temporary saves.

## Sequential puzzle decisions

Each floor now has three decisions. Correct intermediate answers are saved immediately. Closing and reopening a terminal retains the current step. Old checkpoints remain supported. Three accumulated wrong answers still trigger lockdown. Run `verify_puzzle_progress.py` for checkpoint compatibility and `verify_playthrough.py` for the complete movement-driven route.
