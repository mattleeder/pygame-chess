from constants import *
from collections import namedtuple
import pygame
from pygame.locals import *
from window import *
import logging

logging.basicConfig(level = logging.DEBUG)



class Position(namedtuple("Position", ["x", "y"])):
    
    def __add__(self, other):
        if not isinstance(other, Position):
            raise TypeError(f"{other} is type {type(other)} not {type(self)}")
        return Position(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        if not isinstance(other, Position):
            raise TypeError(f"{other} is type {type(other)} not {type(self)}")
        return Position(self[0] - other[0], self[1] - other[1])

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Position(self[0] * other, self[1] * other)
        raise NotImplementedError()

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Position(self[0] / other, self[1] / other)
        raise NotImplementedError()

    def __rtruediv__(self, other):
        raise NotImplementedError()

def direction_vector(point_a : Position, point_b : Position) -> Position:
    "Returns the direction vector from point_a to point_b"
    assert isinstance(point_a, Position), f"Vector is type {type(point_a)}, should be Position"
    assert isinstance(point_b, Position), f"Vector is type {type(point_b)}, should be Position"
    return point_b - point_a

def chess_unit_direction_vector(point_a : Position, point_b : Position) -> Position:
    "Returns a vector from point_a to point_b where the absolute value of the largest component is 1 e.g (8, 8) would become (1, 1)"
    vector = direction_vector(point_a, point_b)
    divisor = max([abs(x) for x in vector])
    assert isinstance(vector, Position), f"Vector is type {type(vector)}, should be Position"
    return vector / divisor

def is_pinnable_vector(vector):
    return vector in PINNABLE_VECTORS

def draw_position(square : Position):
    "Converts board position into drawn position, top left hand corner"
    return square.x * SQUARE_SIZE, (7 - square.y) * SQUARE_SIZE

def get_rect_from_square(square : Position):
    x, y = draw_position(square)
    return pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)

def draw_board():
    colours = [WHITE_SQUARE, BLACK_SQUARE]
    index = -1
    for x in range(0, 8 * SQUARE_SIZE, SQUARE_SIZE):
        index += 1
        for y in range(0, 8 * SQUARE_SIZE, SQUARE_SIZE):
            rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(window, colours[index % 2], rect)
            index += 1

class OutOfBounds(Exception):

    def __init__(self, position : Position, message = None):
        self.position = position
        if message == None:
            self.message = f"{position} not in (0, 0) to (8, 8) range"
        else:
            self.message = message
        super().__init__(self.message)

en_passant_list = [] # Last element is the old position of the en_passant pawn
attacking_king = {
    "White" : set(),
    "Black" : set()
} # Pieces that are attacking enemy king
valid_check_defenses = [] # Moves that save the king
turn = "White"

def turn_gen():
    while True:
        if turn == "White":
            yield "Black"
        yield "White"

get_turn = turn_gen()

PIECE_IMAGE = pygame.image.load(r"images\ChessPiecesArray.png")
PIECE_IMAGE = pygame.Surface.convert_alpha(PIECE_IMAGE)

piece_dict_keys = ["Black Queen", "Black King", "Black Rook", "Black Knight", "Black Bishop", "Black Pawn",
"White Queen", "White King", "White Rook", "White Knight", "White Bishop", "White Pawn"]

piece_images = dict()

for i in range(6):
    for j in range(2):

        x = IMAGE_PIECE_WIDTH * i
        y = IMAGE_PIECE_WIDTH * j

        piece_img = pygame.Rect(x, y, IMAGE_PIECE_WIDTH, IMAGE_PIECE_WIDTH)
        piece_img = PIECE_IMAGE.subsurface(piece_img)
        piece_img = pygame.transform.scale(piece_img, (PIECE_SIZE, PIECE_SIZE))

        piece_images[piece_dict_keys[i + (6 * j)]] = piece_img

del piece_dict_keys
del PIECE_IMAGE