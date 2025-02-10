

```markdown
# TetraFusion

TetraFusion is a modern take on the classic Tetris game, implemented using Python and Pygame. This version introduces new difficulty settings, refined particle effects, and an improved in-game interface while maintaining the classic Tetris feel.

## Features

- **2.5D Block Rendering**: Each Tetris block is rendered with a 3D-like perspective.
- **Dynamic Particle Effects**: Enjoy visually engaging effects triggered by actions like block placement, flame trails, and explosions.
- **Music and Sound Effects**: Background music and sound effects elevate the gaming experience.
- **Custom Music Playlist Support**: Enable a custom playlist by selecting a directory with supported files (`.mp3`, `.wav`, `.flac`, `.ogg`, `.aac`, or `.m4a`).
- **Ghost Piece (Drop Shadow)**: A transparent ghost piece shows where the tetromino will land.
- **Hold Piece Mechanic**: Save a tetromino for later use to strategize your next moves.
- **High Score Tracking**: Save and load high scores along with player initials.
- **Customizable Game Settings**: Adjust grid opacity, key bindings, difficulty (including a new "Very Hard" mode), and other options via an in-game options menu.
- **Subwindow with Stats & Controls**: Displays real-time game statistics, volume control, and track skipping.
- **Smooth User Experience**: Enhanced performance with pre-rendered grid elements and optimized game flow.
- **Tetris Flash Effect**: A visual flash effect when the player clears four lines.

## Requirements

- Python 3.7 or higher
- Pygame 2.0 or higher

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/drDOOM69GAMING/TetraFusion-1.9.0.py.git
   cd TetraFusion-1.9.0.py
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame
   ```

3. **Ensure that the required assets are in place:**

   - **Fonts:**  
     Place `tetris-blocks.TTF` in the `assets` directory.

   - **Audio Files:**  
     Place the following files in the `Audio` directory:
     - Background music: `Background.ogg`
     - Line clear sound: `Lineclear.ogg`
     - Multiple line clear sound: `MultipleLineclear.ogg`
     - Game over sound: `GAMEOVER.ogg`
     - Dramatic grid filling (heartbeat) sound: `heartbeat_grid_almost_full.ogg`

## How to Run

Run the main script using:
```bash
python "TetraFusion 1.9.0.py"
```

## Controls

- **Arrow Keys**: Move the tetromino left/right or rotate (depending on settings).
- **Space**: Hard drop the tetromino.
- **P**: Pause the game.
- **R**: Restart the game.
- **M**: Return to the main menu.
- **Enter**: Start the game from the main menu.
- **Hold Key (default: C)**: Hold the current tetromino for later use.
- **Mouse Click (Subwindow)**: Adjust volume, skip tracks, or activate on-screen buttons.

### In-Game Screens

- **Main Menu:**  
  Displays the title and instructions for starting the game or accessing the options menu.

- **Gameplay:**  
  Features the game grid, real-time score, level, lines cleared, next tetromino preview, and the hold piece display.

- **Options Menu:**  
  Customize controls, difficulty (including the new "Very Hard" mode), grid opacity, visual effects, and music settings (including custom playlist selection).

- **Pause Screen:**  
  Halts the game and displays a resume prompt.

- **Game Over Screen:**  
  Shows your final score and lets you enter your initials if you set a new high score.

## Customization

### Modify Colors
To change the tetromino colors, edit the `COLORS` list in the script:
```python
COLORS = [
    (0, 255, 255), (255, 165, 0), (0, 0, 255),
    (255, 0, 0), (0, 255, 0), (255, 255, 0), (128, 0, 128)
]
```

### Adjust Grid Opacity & Visibility
In the options menu, you can:
- Adjust the grid opacity (0 for invisible up to 192 for semi-transparent).
- Toggle grid lines on or off.

### Replace Audio Files
Swap out the audio files in the `Audio` directory with your own `.ogg` files to change the background music or sound effects.

### Adjust Grid Size
To change the grid dimensions, modify these constants:
```python
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
```

### Enable Custom Music Playlist
In the options menu, select a folder containing supported audio files to enable a custom music playlist.

## High Score System

High scores are saved in `high_score.txt` using the following format:
```
<score> <initials>
```
If the file does not exist, it will be created automatically.

## Screenshots

![Screenshot 2025-01-31 103638](https://github.com/user-attachments/assets/f3605dd9-4ffd-42de-a169-ca6782b672f1)

## Contributing

Contributions are welcome! Please follow these steps:
1. **Fork the repository.**
2. **Create a new branch:**
   ```bash
   git checkout -b feature-name
   ```
3. **Commit your changes:**
   ```bash
   git commit -m "Add feature-name"
   ```
4. **Push to the branch:**
   ```bash
   git push origin feature-name
   ```
5. **Open a pull request.**

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

## Acknowledgments

- Inspired by the classic Tetris game.
- Thanks to the Pygame community for their continued support and resources.
```
