from board import *
from constants import *
from piece import *
from utils import *
from window import *
import sys

piece_manager = PieceManager()
board = ChessBoard(8, piece_manager)
board.setup()

for i, column in enumerate(board.squares):
    print(i)
    for square in column:
        if square.piece:
            print(square.piece)

# Loop forever
while True:

    # Check for and handle events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        piece_manager.handle_event(event)

    # Do any "per frame" actions

    # Clear the window
    window.fill(BLACK)

    # Draw all window elements
    draw_board()
    piece_manager.draw()

    # Update the window
    pygame.display.update()

    # Slow things down a bit
    clock.tick(FRAMES_PER_SECOND)