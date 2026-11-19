# Verification record

Gameplay and voice checks were completed on 18 November 2026, using Windows, Python 3.12.14 and Panda3D 1.10.16. The documents and seven-slide presentation were updated and reviewed on 19 November.

## Algorithms and gameplay

The unit suite passed 28 tests, covering the original calculations, navigation, MDP planning, camera behavior, narration and door interactions. A separate regression check exercised all 24 combinations of three scenarios, four floors and two doors without visiting a terminal first, confirming that a route calculation which closes the current door gives feedback rather than raising a missing-route error.

The integration run completed all four floors in each of the three scenarios through ordinary movement ticks, with path samples checked against game collisions. It also covered the explanation panel, the floor-2 closure, checkpoint restoration and invalid-save handling, while the original quiz campaign passed its success, three-error failure and checkpoint checks.

## Narration and ending

All 66 synthetic narration files loaded in the Windows Panda3D audio manager, and the 6.379-second welcome fits its eight-second opening interval. The bank also passed automatic speech-recognition screening, with flagged cues revised and regenerated, while unknown future lines remain subtitled. Amir selected the voice preview, the screening checks content automatically rather than measuring listener satisfaction.

All three original closing cards appeared in the trainer, followed by the results when Enter was pressed. The standalone Windows build also completed its resource and four-floor route self-check with exit code zero.

## Documents and demonstration

The seven-slide presentation passed package, geometry, font-policy and reimport checks, with its rendered slides reviewed alongside the four-page technical report and the two one-page statements.

The repository's captioned MP4 is 150 seconds long, at 1152 by 720 pixels and 15 frames per second, using application renders and scripted playback without spoken narration.

## Coverage

These checks establish functionality within the supplied scenarios, while participant learning, macOS and Linux runtime behavior, native PowerPoint playback and real building conditions remain outside the recorded evaluation.
