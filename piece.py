from abc import ABC, abstractmethod
from typing import Tuple, Set, List
from window import *
from constants import *
from utils import *

class Piece(ABC):
    _moves : Set[Tuple[int, int]] = None
    _range : int = 8
    can_promote : bool = False
    image = None
    window = window
    
    def __init__(self, colour : str, position : Position, has_moved : bool = False):
        self._colour = colour
        self._rank = self.__class__.__name__
        self.position = position
        self.image = piece_images[f"{self.colour} {self._rank}"]
        self.selected = False
        self.has_moved = has_moved
        self.current_moves : List[Position] = [] 
        self.current_captures : List[Position] = []
        self. current_defending : List[Position] = []

    def _set_manager(self, manager):
        self._piece_manager = manager

    @property
    def colour(self):
        return self._colour

    @property
    def rank(self):
        return self._rank

    @property
    def position(self):
        return self._position

    @position.setter 
    def position(self, new_position):
        if new_position.x > 7 or new_position.y > 7:
            raise OutOfBounds(new_position)
        self._position = new_position

    @property
    def rect(self):
        rect = self.image.get_rect()
        rect[0] = self.loc[0]
        rect[1] = self.loc[1]
        return rect

    def __del__(self) -> None:
        print(f"{self} has been removed")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.colour}, {self.position}, {self._moves})"

    def __str__(self) -> str:
        return f"{self.colour} {self.rank} at {self.position}"

    def possible_moves(self) -> Tuple[List[Position], List[Position]]:
        """Returns moves, captures and defended 
        (Defended squares are squares that are attacked by a piece 
        but not neccessarily able to move to e.g. it's pinned)"""
        moves, captures, defending = self._move_loop()
        if not self.rank == "King" and self.is_pinned():
            logging.debug(f"{self} is pinned")
            # If it is pinned all moves are classed as defending
            # Calculate which moves are still valid
            invalid_moves, moves = self.pinned_validation(moves)
            invalid_captures, captures = self.pinned_validation(captures)
            defending = invalid_moves + invalid_captures + defending
        if self._piece_manager.king_dict[f"{self.colour} King"].in_check:
            moves, invalid_moves = self._check_validation(moves)
            captures, invalid_captures = self._check_validation(captures)
            defending = defending + invalid_moves + invalid_captures

        return moves, captures, defending

    def pinned_validation(self, move_list):

        king_pos = self._piece_manager.king_dict[f"{self.colour} King"].position
        direction_from_king = chess_unit_direction_vector(king_pos, self.position)
        direction_to_king = direction_from_king * -1
        logging.debug(f"Direction to king: {direction_to_king}")
        logging.debug(f"Direction from king: {direction_from_king}")

        valid_moves = []

        for move in move_list[:]:
            move_direction = chess_unit_direction_vector(self.position, move)
            # Check is move is along checking axis
            if move_direction == direction_from_king or move_direction == direction_to_king:
                move_list.remove(move)
                valid_moves.append(move)

        return move_list, valid_moves

    def move(self, pos : Position) -> None:
        logging.debug(f"Moving {self} to {pos}")

        # Move in manager before moving in piece otherwise old position is lost
        self._piece_manager.move(self, pos)
        self.position = pos
        self.has_moved = True

    def _move_loop(self):
        """Loops through moveset and calculates possible moves or captures for the piece
        as well as squares it is defending but can't move to (e.g. defending friendly piece)"""

        moves = []
        captures = []
        defending = []

        for x, y in self._moves:
            magnitude = 1
            while magnitude <= self._range:
                consideration_position = self.position + Position(x, y) * magnitude
                # Ignore if position not on board
                if max(consideration_position) > 7 or min(consideration_position) < 0:
                    break

                # If square if empty, add to moves, if occupied by enemy add to captures, otherwise break
                piece = self._piece_manager.board.square_from_position(consideration_position).piece
                if piece is None:
                    moves.append(consideration_position)
                elif self.colour != piece.colour:
                    if piece.rank != "King":
                        captures.append(consideration_position)
                        break
                    # If piece is enemy king, add squares behind the king to defending
                    defending.append(consideration_position)
                    enemy_colour = "White"
                    if self.colour == "White":
                        enemy_colour = "Black"

                    # Keep track of pieces attacking kings
                    attacking_king[enemy_colour].add(self)

                    while True:
                        magnitude_copy = magnitude + 1
                        consideration_position = self.position + Position(x, y) * magnitude_copy
                        if max(consideration_position) > 7 or min(consideration_position) < 0:
                            break
                        piece = self._piece_manager.board.square_from_position(consideration_position).piece
                        # If no piece, add square to defending then continue
                        if piece is None:
                            defending.append(consideration_position)
                        # If piece and same colour, add to defending then break
                        elif piece.colour == self.colour:
                            defending.append(consideration_position)
                            break
                        # Else break
                        break

                    break

                else:
                    defending.append(consideration_position)
                    break
                magnitude += 1
        
        return moves, captures, defending




    def is_pinned(self) -> bool:
        """Returns true if piece is pinned to friendly king, take care though
        as a pinned piece can still move along the pinned axis or capture attacking piece,
        could get round this by using temporary replacement of moves dict?"""
        king_pos = self._piece_manager.king_dict[f"{self.colour} King"].position
        direction_from_king = chess_unit_direction_vector(king_pos, self.position)
        if not is_pinnable_vector(direction_from_king):
            return False
        
        direction_from_king = Position(int(direction_from_king.x), int(direction_from_king.y))
        direction_to_king = [direction_from_king[0] * -1, direction_from_king[1] * -1]

        # Check for piece in between current piece and king
        magnitude = 1
        pos_to_king = Position(direction_to_king[0], direction_to_king[1])
        while True:
            consideration_position = self.position + (pos_to_king * magnitude)
            piece = self._piece_manager.board.square_from_position(consideration_position).piece
            if consideration_position == king_pos: # Is king
                break
            elif piece is None:
                magnitude += 1
                continue
            else:
                return False

        # Check for enemy piece along checking axis
        magnitude = 1
        pos_from_king = Position(direction_from_king[0], direction_from_king[1])
        while True:
            consideration_position = self.position + (pos_from_king * magnitude)
            if max(consideration_position) > 7 or min(consideration_position) < 0:
                return False
            piece = self._piece_manager.board.square_from_position(consideration_position).piece
            if piece is None:
                magnitude += 1
                continue
            elif piece.colour == self.colour:
                return False
            elif piece.rank in ["King", "Pawn", "Knight"]:
                return False
            elif tuple(direction_to_king) not in piece._moves:
                return False
            return True

    def _check_validation(self, moves):
        """Take moves and make sure they are valid given check status of friendly king
        Returns valid_moves, invalid_moves"""
        valid_moves = []
        invalid_moves = []
        if self.rank == "King":
            return moves, invalid_moves
        if self._piece_manager.king_dict[f"{self.colour} King"].in_check:
            logging.debug(f"{self}: My King is in check")
            # If in double check, only King can move
            if len(attacking_king[self.colour]) == 2:
                invalid_moves = moves
                return [], invalid_moves
            # If only 1 piece attacking king, next move must block piece, capture piece or move king
            else:
                for move in moves:
                    if move in valid_check_defenses:
                        valid_moves.append(move)
                    else:
                        invalid_moves.append(move)

        return valid_moves, invalid_moves
            
    def pinned_moves(self):
        "Calculates moves available to pinned piece, e.g. moving along checking axis and capturing attacking piece"
        pass

    def give_check(self) -> bool:
        "Returns true if piece gives check to enemy king"
        pass

    def destroy(self) -> None:
        "Remove a piece from play, undraw it and remove references to it"
        self._piece_manager.pieces[self.colour].remove(self)
        # Should also remove it from the square it's on

    @property
    def loc(self):
        return [self.position.x * 128, (7 - self.position.y) * 128]

    def draw(self) -> None:

        if self.selected:

            # Piece highlight
            rect = self.loc + [SQUARE_SIZE, SQUARE_SIZE]
            pygame.draw.rect(self.window, MOVE_COLOUR, rect, 0)

            # Draw current moves
            radius = PIECE_SIZE / 2
            for move in self.current_moves:
                x, y = draw_position(move)
                circle_centre = [x + radius, y + radius]
                pygame.draw.circle(self.window, MOVE_COLOUR, circle_centre, radius, 0)
            for capture in self.current_captures:
                x, y = draw_position(capture)
                circle_centre = [x + radius, y + radius]
                pygame.draw.circle(self.window, CAPTURE_COLOUR, circle_centre, radius, 0)


        self.window.blit(self.image, self.loc)

    def handle_event(self, event):

        if not event.type == MOUSEBUTTONDOWN:
            return False

        if self.selected:
            # Check if clicked on valid move
            for move in self.current_moves + self.current_captures:
                valid = get_rect_from_square(move).collidepoint(event.pos)
                if valid:
                    # PRE MOVE EVENTS

                    # Clear en_passant_list
                    logging.debug("Clearing en_passant_list")
                    global en_passant_list
                    en_passant_list.clear()

                    # Check for castling
                    if self.rank == "King":
                        # Left rook
                        if self.position.x - move.x == 2:
                            left_rook = self._piece_manager.board.square_from_position(self.position + Position(-4, 0)).piece
                            left_rook.move(self.position + Position(-1, 0))
                            left_rook.has_moved = True
                        # Right rook
                        elif self.position.x - move.x == -2:
                            right_rook = self._piece_manager.board.square_from_position(self.position + Position(3, 0)).piece
                            right_rook.move(self.position + Position(1, 0))
                            right_rook.has_moved = True
                    
                    # Check for en passant
                    elif self.rank == "Pawn":
                        # If moved 2, add enemy pawns to en_passant_list
                        if abs(self.position.y - move.y) == 2:
                            left_piece_position = move + Position(-1, 0)
                            if left_piece_position.x >= 0:
                                left_piece = self._piece_manager.board.square_from_position(left_piece_position).piece
                                if left_piece and left_piece.rank == "Pawn" and left_piece.colour != self.colour:
                                    en_passant_list.append(left_piece)

                            right_piece_position = move + Position(1, 0)
                            if right_piece_position.x <= 7:
                                right_piece = self._piece_manager.board.square_from_position(right_piece_position).piece
                                if right_piece and right_piece.rank == "Pawn" and right_piece.colour != self.colour:
                                    en_passant_list.append(right_piece)

                            en_passant_list.append(self.position)

                        # Check if capturing en_passant, pawn has moved left or right and then not captured a piece
                        elif move.x - self.position.x in (1, -1) and not self._piece_manager.board.square_from_position(move).piece:
                            captured_piece_position = move - Position(next(iter(self._moves))[0], next(iter(self._moves))[1]) # Retrieves the single move for a pawn
                            piece = self._piece_manager.board.square_from_position(captured_piece_position).piece
                            piece.destroy()
                            self._piece_manager.board.square_from_position(captured_piece_position).remove()

                        logging.debug(f"En passant list is now: {en_passant_list}")

                    self.move(move)
                    # Check for promotion
                    self.selected = False
                    global turn
                    turn = next(get_turn)

                    # POST MOVE EVENTS
                    if self.rank == "Pawn":
                        self.promote()
                    return self._post_move()

            self.selected = False
            return False

        event_point_on_piece = self.rect.collidepoint(event.pos)

        if not event_point_on_piece:
            return False

        if self.colour != turn:
            return False

        self.selected = True
        self.current_moves, self.current_captures, self.current_defending = self.possible_moves()

    def _post_move(self):
        global attacking_king
        attacking_king["White"].clear()
        attacking_king["Black"].clear()

        # Update square control
        self._piece_manager.board._evaluate_square_control("Black")
        self._piece_manager.board._evaluate_square_control("White")

        # Swap turns
        # Check for checks
        global valid_check_defenses
        valid_check_defenses.clear()

        enemy_colour = "White"
        if self.colour == "White":
            enemy_colour = "Black"

        king = self._piece_manager.king_dict[f"{enemy_colour} King"]
        if king.in_check:
            if len(attacking_king[enemy_colour]) == 1:
                attacker = next(iter(attacking_king[enemy_colour])) # get attacking piece
                direction_vector = chess_unit_direction_vector(attacker.position, king.position)
                valid_check_defenses.append(attacker.position)
                magnitude = 1
                while True:
                    new_move = attacker.position + direction_vector * magnitude
                    logging.debug(new_move)
                    # If there is a piece, it is the king
                    if self._piece_manager.board.square_from_position(new_move).piece:
                        break
                    valid_check_defenses.append(new_move)
                    magnitude += 1

        # Check for checkmate
        self._piece_manager.checkmate_calculator(enemy_colour)
        return True

class Bishop(Piece):

    _moves = set([
        tuple([1, 1]),
        tuple([-1, 1]),
        tuple([-1, -1]),
        tuple([1, -1])
        ])

class Knight(Piece):

    _moves = set(
        [tuple([1, 2]), 
        tuple([2, 1]), 
        tuple([-1, 2]), 
        tuple([-2, 1]), 
        tuple([1, -2]), 
        tuple([2, -1]), 
        tuple([-1, -2]), 
        tuple([-2, -1])]
    )
    _range = 1

class Rook(Piece):

    _moves = set(
        [tuple([1, 0]), 
        tuple([0, 1]), 
        tuple([-1, 0]), 
        tuple([0, -1])]
    )

class Queen(Piece):

    _moves = set(
        [tuple([1, 0]), 
        tuple([0, 1]), 
        tuple([1, 1]), 
        tuple([-1, 1]), 
        tuple([-1, 0]), 
        tuple([0, -1]), 
        tuple([1, -1]), 
        tuple([-1, -1])]
    )

class King(Piece):

    _moves = set(
        [tuple([1, 0]), 
        tuple([0, 1]),
        tuple([1, 1]),
        tuple([-1, 1]), 
        tuple([-1, 0]), 
        tuple([0, -1]),
        tuple([1, -1]), 
        tuple([-1, -1])]
    )
    _range = 1

    # def __init__(self, colour : str, position : Position, has_moved : bool = False):
    #     super().__init__(colour, position, has_moved)
    #     self.in_check = False

    @property
    def in_check(self):
        enemy_colour = "White"
        if self.colour == "White":
            enemy_colour = "Black"
        return self._piece_manager.board.square_from_position(self.position).control[enemy_colour]

    def _move_loop(self):
        """Loops through moveset and calculates possible moves or captures for the piece
        as well as squares it is defending but can't move to (e.g. defending friendly piece)"""

        moves, captures, defending = super()._move_loop()

        enemy_colour = "White"
        if self.colour == "White":
            enemy_colour = "Black"

        # Validate moves and captures
        moves = self._king_move_validation(moves, enemy_colour)
        captures = self._king_move_validation(captures, enemy_colour)

        if self.in_check:
            logging.debug(f"{self} in check")
        if self.has_moved or self.in_check:
            return moves, captures, defending

        # Castling
        # Check if left rook has moved
        # Check if no pieces between king and left rook
        # Check if no enemy square control between king and left rook
        # Repeat for right rook

        # Left rook
        left_rook_position = self.position + Position(-4, 0)
        left_rook = self._piece_manager.board.square_from_position(left_rook_position).piece

        left_rook_can_castle = True

        if left_rook and not left_rook.has_moved:
            for i in range(1, 4):
                square = self._piece_manager.board.square_from_position(self.position + Position(-i, 0))
                # If piece in the way or moving through check, cannot castle
                if square.piece or square.control[enemy_colour]:
                    left_rook_can_castle = False
                    break
        else:
            left_rook_can_castle = False

        if left_rook_can_castle:
            moves.append(self.position + Position(-2, 0))

        # Right rook
        right_rook_position = self.position + Position(3, 0)
        right_rook = self._piece_manager.board.square_from_position(right_rook_position).piece

        right_rook_can_castle = True

        if right_rook and not right_rook.has_moved:
            for i in range(1, 3):
                square = self._piece_manager.board.square_from_position(self.position + Position(i, 0))
                # If piece in the way or moving through check, cannot castle
                if square.piece or square.control[enemy_colour]:
                    right_rook_can_castle = False
                    break
        else:
            right_rook_can_castle = False

        if right_rook_can_castle:
            moves.append(self.position + Position(2, 0))

        return moves, captures, defending

    def _king_move_validation(self, move_list : List[Position], enemy_colour : str):


        # Normal Moves
        for move in move_list[:]:
            if self._piece_manager.board.square_from_position(move).control[enemy_colour]:
                move_list.remove(move)

        return move_list



class Pawn(Piece):

    move_dict = {
        "White" : set([tuple([0, 1])]),
        "Black" : set([tuple([0, -1])])
    }

    @property
    def _range(self):
        return 2 - self.has_moved

    @property
    def _moves(self):
        return self.move_dict[self.colour]

    def promote(self):
        if self.position.y == 0 or self.position.y == 7:
            logging.debug(f"{self} promotion")
            self._piece_manager.promote = [self]

    # Pawns need a different _move_loop
    def _move_loop(self):
        """Loops through moveset and calculates possible moves or captures for the piece
        as well as squares it is defending but can't move to (e.g. defending friendly piece)"""

        move = next(iter(self._moves)) # One member set

        moves, _, _ = super()._move_loop()
        captures = []
        defending = []
        
        left_capture = self.position + Position(move[0], move[1]) + Position(-1, 0)
        right_capture = self.position + Position(move[0], move[1]) + Position(1, 0) 

        for capture in [left_capture, right_capture]:
            if max(capture) <= 7 and min(capture) >= 0:
                square = self._piece_manager.board.square_from_position(capture).piece
                if square is not None and square.colour!= self.colour:
                    captures.append(capture)
                else:
                    defending.append(capture)

        # Check En Passant
        if self in en_passant_list:
            enemy_pos = en_passant_list[-1]
            en_passant_move = enemy_pos - Position(next(iter(self._moves))[0], next(iter(self._moves))[1]) # enemy pos + current pawn y movement
            captures.append(en_passant_move)
            logging.debug(f"En passant captures: {captures}")

        return moves, captures, defending

class PieceManager():
    
    def __init__(self):
        self.pieces = {
            "Black" : [],
            "White" : []
        }
        self.king_dict = {
            "White King" : None,
            "Black King" : None,
        }
        self.promote = []
        self.promotion_rect = None
        self.promotion_order = None

    def set_board(self, board):
        self.board = board

    def create_piece(self, PieceClass : Piece, colour : str, position : Position):
        piece = PieceClass(colour, position)
        piece._set_manager(self)
        self.pieces[colour].append(piece)
        if piece.rank == "King":
            self.king_dict[f"{colour} King"] = piece
        return piece

    def draw(self):
        for piece in self.pieces["Black"] + self.pieces["White"]:
            piece.draw()
        if self.promote:
            self.create_promotion_overlay()


    def handle_event(self, event):
        if self.promote:
            if event.type == MOUSEBUTTONDOWN  and self.promotion_rect.collidepoint(event.pos):
                index = (event.pos[1] - self.promotion_rect.top) // 128
                rank = self.promotion_order[index]
                logging.debug(f"Promote {self.promote[0]} to {rank}")
                pos = self.promote[0].position
                colour = self.promote[0].colour
                rank_dict = {
                    "Queen" : Queen,
                    "Knight" : Knight,
                    "Bishop" : Bishop,
                    "Rook" : Rook
                }
                self.promote[0].destroy()
                self.promote.clear()
                self.promotion_rect = None
                self.promotion_order = None
                piece = self.create_piece(rank_dict[rank], colour, pos)
                piece.has_moved = True
                self.board.square_from_position(pos).place(piece)
                piece._post_move()

        # Make sure to call post move methods after promotion e.g. evaluate_square_control
        else:
            for piece in self.pieces["Black"] + self.pieces["White"]:
                piece.handle_event(event)

    def create_promotion_overlay(self):
        location = self.promote[0].position
        if location.y == 0:
            location = Position(location.x, 3)
        
        rect = pygame.Rect(location.x * SQUARE_SIZE, (7 - location.y) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE * 4)
        pygame.draw.rect(window, (55, 55, 55), rect)
        draw_order = ["Queen", "Knight", "Rook", "Bishop"]
        colour = self.promote[0].colour
        if colour == "Black":
            draw_order.reverse()
        for i, rank in enumerate(draw_order):
            image = piece_images[f"{colour} {rank}"]
            self.promote[0].window.blit(image, (location.x * SQUARE_SIZE, ((7 - location.y) + i) * SQUARE_SIZE))

        self.promotion_rect = rect
        self.promotion_order = draw_order


    def move(self, piece, new_position):
        self.board.move(piece, new_position)

    def checkmate_calculator(self, colour):
        valid_moves = []
        for piece in self.pieces[colour]:
            moves, captures, defending = piece.possible_moves()
            valid_moves = valid_moves + moves + captures

        logging.debug(f"Number of valid moves for {colour}: {len(valid_moves)}")

        if len(valid_moves) == 0:
            logging.debug(f"=============================")
            if self.king_dict[f"{colour} King"].in_check:
                logging.debug(f"{colour} has been checkmated!")
            else:
                logging.debug("Stalemate")