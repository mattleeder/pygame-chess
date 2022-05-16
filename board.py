import logging
from utils import *
from piece import *

class ChessSquare:
    
    def __init__(self, piece = None):
        self.control = {
            "White" : False,
            "Black" : False
        }
        self.piece = piece

    def place(self, piece):
        self.piece = piece

    def remove(self):
        self.piece = None

class ChessBoard:
    
    def __init__(self, n, piece_manager):
        self.limit = n - 1
        self.piece_manager = piece_manager
        self.squares = [[0] * n for _ in range(n)]
        for row in range(n):
            for col in range(n):
                self.squares[row][col] = ChessSquare()

    def move(self, piece : Piece, new_position : Position):
        old_square = self.square_from_position(piece.position)
        new_square = self.square_from_position(new_position)
        logging.debug(new_position)
        logging.debug(piece.position)

        if new_square.piece:
            logging.debug(f"Destroying {new_square.piece}")
            new_square.piece.destroy()

        old_square.remove()
        new_square.place(piece)


    def setup(self):

        self.piece_manager.set_board(self)

        for i, colour in enumerate(["White", "Black"]):
            for j in range(8):
                pawn = self.piece_manager.create_piece(Pawn, colour, Position(j, 1 + (i * 5)))
                self.squares[j][1 + (i * 5)].place(pawn)

            for j, item in enumerate([Rook, Knight, Bishop]):
                piece = self.piece_manager.create_piece(item, colour, Position(j, i * 7))
                self.squares[j][i * 7].place(piece)

                piece = self.piece_manager.create_piece(item, colour, Position(7 - j, i * 7))
                self.squares[7 - j][i * 7].place(piece)

            queen = self.piece_manager.create_piece(Queen, colour, Position(3, i * 7))
            self.squares[3][i * 7].place(queen)

            king = self.piece_manager.create_piece(King, colour, Position(4, i * 7))
            self.squares[4][i * 7].place(king)

    def square_from_position(self, position : Position):
        return self.squares[int(position.x)][int(position.y)]

    def _evaluate_square_control(self, colour):
        "Mark the squares controlled by colour"

        # Reset square control for colour
        for row in range(self.limit + 1):
            for col in range(self.limit + 1):
                self.squares[row][col].control[colour] = False

        for piece in self.piece_manager.pieces[colour]:
            for col in range(self.limit + 1):
                if piece.rank == "King":
                    # Make sure to avoid infinite loop
                    moves = []
                    for move in piece._moves:
                        pos = Position(piece.position.x + move[0], piece.position.y + move[1])
                        if max(pos) <= 7 and min(pos) >= 0:
                            moves.append(pos)
                else:
                    moves, captures, defending = piece.possible_moves()
                    if piece.rank == "Pawn":
                        moves = []

                assert isinstance(moves, list)
                assert isinstance(captures, list)
                assert isinstance(defending, list)

                for position in moves + captures + defending:
                    if position.x == 5 and position.y == 1:
                        logging.warning(f"Setting {position} to {colour} control")
                    self.squares[position.x][position.y].control[colour] = True