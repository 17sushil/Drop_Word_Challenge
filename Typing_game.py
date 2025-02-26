from flask import Flask, render_template_string
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# HTML template with embedded CSS and JavaScript
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Typing Game</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #gameCanvas {
            border: 2px solid var(--bs-secondary);
            background-color: var(--bs-dark);
            width: 800px;
            height: 600px;
            max-width: 100%;
        }
        .game-header {
            display: flex;
            justify-content: center;
            gap: 2rem;
        }
    </style>
</head>
<body>
    <div class="container my-4">
        <div id="menu" class="text-center">
            <h1 class="mb-4">Typing Game</h1>
            <div class="difficulty-buttons">
                <button class="btn btn-lg btn-secondary mx-2" onclick="startGame('easy')">Easy</button>
                <button class="btn btn-lg btn-secondary mx-2" onclick="startGame('medium')">Medium</button>
                <button class="btn btn-lg btn-secondary mx-2" onclick="startGame('hard')">Hard</button>
            </div>
        </div>

        <div id="game" class="text-center d-none">
            <div class="game-header mb-3">
                <span class="h4">Score: <span id="score">0</span></span>
                <span class="h4 ms-4">Level: <span id="level">Easy</span></span>
            </div>
            <canvas id="gameCanvas"></canvas>
            <div class="mt-3">
                <button id="restartBtn" class="btn btn-secondary" onclick="restartGame()">Restart</button>
            </div>
        </div>

        <div id="gameOver" class="text-center d-none">
            <h2>Game Over!</h2>
            <p class="h4">Final Score: <span id="finalScore">0</span></p>
            <button class="btn btn-secondary mt-3" onclick="showMenu()">Play Again</button>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
    <script>
        // Audio Manager
        class AudioManager {
            constructor() {
                this.synth = new Tone.Synth().toDestination();
                this.successNotes = ['C4', 'E4', 'G4'];
                this.failNote = 'A3';
            }

            playTypeSound() {
                this.synth.triggerAttackRelease('C4', '0.1');
            }

            playSuccessSound() {
                const note = this.successNotes[Math.floor(Math.random() * this.successNotes.length)];
                this.synth.triggerAttackRelease(note, '0.15');
            }

            playGameOverSound() {
                this.synth.triggerAttackRelease(this.failNote, '0.3');
            }
        }

        const audioManager = new AudioManager();

        // Game Logic
        class TypingGame {
            constructor() {
                this.canvas = document.getElementById('gameCanvas');
                this.ctx = this.canvas.getContext('2d');
                this.words = [];
                this.score = 0;
                this.currentDifficulty = '';
                this.gameRunning = false;
                this.currentInput = '';
                this.wordSpawnInterval = null;

                // Set canvas size
                this.canvas.width = 800;
                this.canvas.height = 600;

                // Bind events
                document.addEventListener('keydown', this.handleKeyPress.bind(this));
            }

            async initialize(difficulty) {
                // Clear any existing game state
                this.stopGame();

                // Reset game state
                this.currentDifficulty = difficulty;
                this.score = 0;
                this.words = [];
                this.currentInput = '';
                this.gameRunning = true;

                // Get words from server
                const response = await fetch(`/words/${difficulty}`);
                const data = await response.json();
                this.wordList = data.words;

                // Start game loop
                this.gameLoop();
                // Start word spawning
                this.wordSpawnInterval = setInterval(() => this.spawnWord(), 2000);
            }

            stopGame() {
                this.gameRunning = false;
                if (this.wordSpawnInterval) {
                    clearInterval(this.wordSpawnInterval);
                    this.wordSpawnInterval = null;
                }
                this.words = [];
                // Clear the canvas
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            }

            spawnWord() {
                if (!this.gameRunning) return;

                const word = this.wordList[Math.floor(Math.random() * this.wordList.length)];
                const x = Math.random() * (this.canvas.width - 100);

                this.words.push({
                    text: word,
                    x: x,
                    y: 0,
                    speed: Math.max(1, 4 - word.length * 0.2)
                });
            }

            handleKeyPress(event) {
                if (!this.gameRunning) return;

                if (event.key === 'Backspace') {
                    this.currentInput = this.currentInput.slice(0, -1);
                } else if (event.key.length === 1) {
                    this.currentInput += event.key;
                    audioManager.playTypeSound();

                    // Check if current input matches any words
                    const matchedWordIndex = this.words.findIndex(word => word.text === this.currentInput);
                    if (matchedWordIndex !== -1) {
                        // Get the word and update score
                        const word = this.words[matchedWordIndex];
                        this.score += word.text.length * 10;

                        // Immediately remove the word from the array
                        this.words.splice(matchedWordIndex, 1);

                        // Reset current input
                        this.currentInput = '';

                        // Play success sound and update score display
                        audioManager.playSuccessSound();
                        document.getElementById('score').textContent = this.score;
                    }
                }
            }

            gameLoop() {
                if (!this.gameRunning) return;

                // Clear canvas
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

                // Update and draw words
                this.ctx.font = '24px Arial';
                this.ctx.fillStyle = '#ffffff';

                for (let i = this.words.length - 1; i >= 0; i--) {
                    const word = this.words[i];
                    word.y += word.speed;

                    // Check if word hit bottom
                    if (word.y > this.canvas.height) {
                        this.gameOver();
                        return;
                    }

                    // Draw word
                    this.ctx.fillText(word.text, word.x, word.y);
                }

                // Draw current input
                this.ctx.fillStyle = '#4CAF50';
                this.ctx.fillText(this.currentInput, 10, this.canvas.height - 30);

                requestAnimationFrame(() => this.gameLoop());
            }

            gameOver() {
                this.stopGame();
                audioManager.playGameOverSound();

                document.getElementById('game').classList.add('d-none');
                document.getElementById('gameOver').classList.remove('d-none');
                document.getElementById('finalScore').textContent = this.score;
            }
        }

        const game = new TypingGame();

        function startGame(difficulty) {
            document.getElementById('menu').classList.add('d-none');
            document.getElementById('gameOver').classList.add('d-none');
            document.getElementById('game').classList.remove('d-none');
            document.getElementById('level').textContent = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
            game.initialize(difficulty);
        }

        function showMenu() {
            game.stopGame();
            document.getElementById('gameOver').classList.add('d-none');
            document.getElementById('game').classList.add('d-none');
            document.getElementById('menu').classList.remove('d-none');
        }

        function restartGame() {
            game.initialize(game.currentDifficulty);
        }
    </script>
</body>
</html>
'''

def get_words(difficulty):
    word_lists = {
        'easy': [
            'cat', 'dog', 'run', 'jump', 'play', 'house', 'tree', 'book', 'fish', 'bird',
            'sky', 'sun', 'moon', 'star', 'rain', 'snow', 'wind', 'food', 'cake', 'milk',
            'bed', 'desk', 'door', 'wall', 'lamp', 'ball', 'park', 'shop', 'bike', 'hand',
            'foot', 'head', 'face', 'nose', 'eyes', 'song', 'game', 'time', 'blue', 'green',
            'red', 'gold', 'pink', 'smile', 'laugh', 'dance', 'walk', 'talk', 'eat', 'drink'
        ],
        'medium': [
            'python', 'garden', 'window', 'picture', 'computer', 'keyboard', 'mountain',
            'butterfly', 'sunshine', 'rainbow', 'printer', 'monitor', 'pencil', 'library',
            'building', 'chocolate', 'airplane', 'birthday', 'sandwich', 'weekend', 'morning',
            'evening', 'cooking', 'drawing', 'running', 'dancing', 'singing', 'playing',
            'dolphin', 'penguin', 'turtle', 'rabbit', 'monkey', 'giraffe', 'peacock'
        ],
        'hard': [
            'algorithm', 'programming', 'dictionary', 'javascript', 'development',
            'technology', 'experience', 'understanding', 'communication', 'organization',
            'environment', 'imagination', 'preparation', 'celebration', 'achievement',
            'performance', 'competition', 'exploration', 'innovation', 'inspiration',
            'motivation', 'dedication', 'concentration', 'determination', 'appreciation'
        ]
    }
    return random.sample(word_lists[difficulty], min(50, len(word_lists[difficulty])))

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/words/<difficulty>')
def words(difficulty):
    return {'words': get_words(difficulty)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
