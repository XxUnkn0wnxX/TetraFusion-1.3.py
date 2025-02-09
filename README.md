# TetraFusion

TetraFusion is a modern take on the classic Tetris game, implemented using Python and Pygame. The game features 2.5D graphics, dynamic particle effects, background music, and a user-friendly interface.

## Features

- **2.5D Block Rendering**: Each Tetris block is rendered with a 3D-like perspective.
- **Dynamic Particle Effects**: Visual effects triggered by actions like block placement.
- **Music and Sound Effects**: Background music and sound effects enhance the gaming experience.
- **Custom Music Playlist Support**: Users can enable a custom playlist by selecting a directory with `.mp3`, `.wav`, `.flac`, `.ogg`, `.aac`, or `.m4a` files.
- **Ghost Piece (Drop Shadow)**: A transparent "ghost piece" shows where the tetromino will land. [Broken Feature]
- **High Score Tracking**: Save and load high scores with player initials.
- **Customizable Game Settings**: Adjust grid opacity, key bindings, and difficulty.
- **Flame Trail Effects**: Dynamic effects when moving pieces.
- **Subwindow with Stats & Controls**: Displays real-time game statistics, volume control, and track skipping.
- **Smooth User Experience**: Optimized performance with pre-rendered grid and enhanced game flow.
- **Tetris Flash Effect**: A visual flash occurs when a player clears four lines.
- **New Difficulty Settings**: Includes an extra "Very Hard" mode.

## Requirements

- Python 3.7 or higher
- Pygame 2.0 or higher

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/drDOOM69GAMING/TetraFusion-1.3.py.git
   cd TetraFusion-1.3.py
   ```

2. Install dependencies:
   ```bash
   pip install pygame
   ```

3. Ensure the required assets (e.g., fonts, audio files) are in the correct directories:
   - **Fonts:** `assets/tetris-blocks.TTF`
   - **Audio:**
     - Background music: `Audio/Background.ogg`
     - Line clear sound: `Audio/Lineclear.ogg`
     - Multiple line clear sound: `Audio/MultipleLineclear.ogg`
     - Game over sound: `Audio/GAMEOVER.ogg`
     - Dramatic grid filling sound: `Audio/heartbeat_grid_almost_full.ogg`

## How to Run

Run the main script:
```bash
python "TetraFusion 1.8.2.py"
```

## Controls

- **Arrow Keys**: Move and rotate the tetromino.
- **Space**: Hard drop.
- **P**: Pause the game.
- **R**: Restart the game.
- **M**: Return to the main menu.
- **Enter**: Start the game from the main menu.
- **Mouse Click (Subwindow)**: Adjust volume and skip tracks.

### Main Menu
- Displays the title and instructions to start the game.

### Gameplay
- Features the grid, real-time score, level, lines cleared, and the next tetromino preview.

### Pause Screen
- Pauses the game and displays a message to resume.

### Game Over Screen
- Shows the player's score and allows saving initials for high scores.

## Customization

### Modify Colors
Edit the `COLORS` list to change tetromino colors.
```python
COLORS = [(0, 255, 255), (255, 165, 0), (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (128, 0, 128)]
```

### Adjust Grid Opacity & Visibility
In the **options menu**, you can:
- Adjust grid opacity from **0 (invisible) to 192 (semi-transparent).**
- Toggle grid lines on/off.

### Replace Audio
Replace files in the `Audio` directory with your own `.ogg` files.

### Adjust Grid Size
Modify `SCREEN_WIDTH`, `SCREEN_HEIGHT`, and `BLOCK_SIZE` to change the grid dimensions.
```python
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
```

### Enable Custom Music Playlist
To enable custom music, go to the **options menu** and select a folder containing supported music files.

## High Score System

High scores are saved to `high_score.txt` in the following format:
```
<score> <initials>
```
If the file is not found, it will be created automatically.

## Screenshots

![Screenshot 2025-01-31 103638](https://github.com/user-attachments/assets/f3605dd9-4ffd-42de-a169-ca6782b672f1)

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

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
- Thanks to the Pygame community for their support and resources.

