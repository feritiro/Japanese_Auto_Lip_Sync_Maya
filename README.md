# Auto Lip Sync Animation for Autodesk Maya

![Auto Lip Sync Demo](scripts\test_sample/MayaAutoLipSync.gif)
https://youtu.be/XVH0S4Lm_3M

This project automates the creation of facial keyframe animations in Autodesk Maya based on audio input. It integrates forced phoneme alignment and speech emotion recognition (SER) to generate expressive and synchronized lip sync animations.

## Key Features

- Automatic phoneme detection using Montreal Forced Aligner (MFA)
- Optional Emotion classification using a deep learning model (e.g., Happy, Neutral, Angry)
- Support for Japanese and English audio inputs
- Generation of keyframes in Maya based on phoneme and emotion alignment

## Dependencies

### Conda Environments

The project uses two isolated conda environments: one for forced alignment and another for emotion recognition.

#### Environment: `aligner` (MFA)

```bash
conda create -n aligner python=3.8
conda activate aligner
pip install montreal-forced-aligner

conda create -n ser python=3.8
conda activate ser
pip install tensorflow keras librosa numpy soundfile

## Project Structure
auto_lip_sync/
├── assets/                  # Phoneme and emotion pose files
├── input/                   # Temporary input folder (audio + transcript)
├── output/                  # Contains aligned TextGrid from MFA
├── models/                  # Pretrained emotion recognition model
├── auto_lip_sync/           # Source code
│   └── auto_lip_sync.py     # Main animation logic
├── scripts/                 # MFA lexicon and language model
├── test_sample/             # Example files for testing
├── .gitignore
└── README.md
