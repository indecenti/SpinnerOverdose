<img width="1920" height="728" alt="spinner_overdose_logo" src="https://github.com/user-attachments/assets/f532bf31-70a3-4d96-a253-b036117aa408" />

# Spinner Overdose - Arcade Mini Game Engine

A complete arcade game engine built with Pygame featuring a spinner-based input system, multiple mini-games, high score tracking, and procedural audio synthesis.

## Features

### Core Engine
- **Adaptive Display System**: Automatic resolution detection (1920x1080 or 1280x720) with letterboxing
- **Spinner Input**: Mouse-based rotary controller emulation with configurable sensitivity
- **State Management**: Clean state machine architecture for menu navigation and game flow
- **Procedural Audio**: Real-time sound synthesis using NumPy (no external audio files required)
- **High Score System**: Persistent JSON-based leaderboards with arcade-style name entry

### Mini-Games
The engine includes a complete **Breakout Spinner** implementation featuring:
- 20 progressively challenging levels with 10 unique brick patterns
- 8 power-ups (multiball, big paddle, slow ball, fireball, magnet, laser, extra life, score boost)
- Combo system with score multipliers
- Lives system with visual feedback
- Particle effects and screen shake

### Audio System
Custom `SoundSynthesizer` generates all game sounds procedurally:
- Waveform types: sine, square, sawtooth, triangle
- ADSR envelope shaping
- Sound caching for performance
- 15+ distinct sound effects (blips, explosions, power-ups, game over, etc.)

### Visual Components
- **Animated Backgrounds**: Parallax star fields with speed lines
- **Menu Carousel**: Smooth 3D-style game selection with transitions
- **Particle Systems**: Explosions, sparkles, and trail effects
- **HUD**: Minimal arcade-style heads-up display


<img width="1276" height="720" alt="image" src="https://github.com/user-attachments/assets/8ea91956-e7d3-4dc6-a6b6-6f121b294af4" />


<img width="1272" height="717" alt="image" src="https://github.com/user-attachments/assets/463b6eaa-cb8e-4243-82af-4df24999dba5" />


<img width="1271" height="716" alt="image" src="https://github.com/user-attachments/assets/13930671-e9ba-4433-938b-48ee647ef8fa" />


## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spinner-overdose.git
cd spinner-overdose

# Install dependencies
pip install pygame numpy

# Run the game
python main.py
