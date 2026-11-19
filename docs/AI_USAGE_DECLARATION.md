# AI Usage Declaration

Project: Alem AI Evacuation Trainer  
Team members: Amir and Adilzhan  
Date: 19 November 2026

## Original project and later revision

Our project builds on the original game developed by Adilzhan before the current revision, and the AI assistance described below relates to the later evacuation-training extension and its submission materials.

## Development assistance

We used ChatGPT and Codex to develop the extension, including code generation for the training controller and sequential MDP, debugging, preparation and execution of automated checks, and drafting of documentation and presentation materials. This assistance also covered launch compatibility and the door interaction bug, while the original game provided the 3D environment and gameplay foundation.

## Voice and runtime

Amir provided a voice reference and selected the final synthetic voice, which was generated with F5-TTS v1 Base and Vocos. The resulting audio files are included locally, with model and voice attribution in audio/adeka_f5/CREDITS.txt.

During gameplay, A* search, Bayesian inference and MDP value iteration run locally, without calls to ChatGPT or another language-model service. The scenario probabilities are synthetic model inputs, and the original asset attributions remain included with the project.
