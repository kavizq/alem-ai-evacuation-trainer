# Verification record

18 November 2026. Windows, Python 3.12.14, Panda3D 1.10.16.

- 26 unit tests passed, including the original algorithm, navigation and camera tests, the new MDP tests, four narration checks and three door-without-terminal regression checks.
- All 24 combinations of three scenarios, four floors and two doors were exercised without first visiting the terminal. No exceptions occurred. A route calculation that closes the current door now shows an unavailable-exit message instead of recording a missing route length.
- All four floors in all three training scenarios completed using ordinary movement ticks. Path samples were checked against actual game collisions.
- The live floor-2 exit closure selected a new available exit. Its state survived a checkpoint round trip.
- Original narration played through a valid Windows Panda3D audio manager. A new Windows speech message finished successfully. All three exact original closing cards were rendered in the trainer, and Enter opened the results.
- Invalid training checkpoint data left the current session unchanged.
- The preserved original quiz campaign passed its four-floor success, three-error failure and checkpoint restoration checks.
- The standalone Windows build completed its resource and route self-check on all four floors, with exit code zero.
- The six-slide PPTX passed package, geometry, font-policy and first-party reimport checks. Every slide was inspected visually.
- The four-page technical report and both one-page statements were rendered and inspected.
- The MP4 has a measured duration of 150 seconds, resolution 1152 by 720 and 15 frames per second. Selected frames were inspected. It uses scripted application playback and captions; it has no spoken narration.

These checks were run by Codex. They do not replace student review, a user study, macOS/Linux verification, native PowerPoint playback testing or real building validation.
