import pygame
import sys

# Inicializar Pygame
pygame.init()

# Constantes
CELL_SIZE = 70
GRID_MARGIN = 80
FONT_SIZE = 28
FONT_SIZE_SMALL = 20
BACKGROUND_COLOR = (240, 240, 245)
GRID_COLOR = (180, 180, 190)
ISLAND_COLOR = (70, 130, 180)
ISLAND_BORDER = (50, 100, 150)
BRIDGE_COLOR = (100, 70, 40)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 140, 0)
INFO_COLOR = (60, 60, 60)
SUCCESS_COLOR = (50, 205, 50)
ERROR_COLOR = (220, 20, 60)


class HashiwokakeroGame:
    def __init__(self, filename):
        self.load_board(filename)
        self.selected_island = None
        self.bridges = []  # Lista de puentes: (start_pos, end_pos, count)
        self.screen_width = self.cols * CELL_SIZE + 2 * GRID_MARGIN
        self.screen_height = self.rows * CELL_SIZE + 2 * GRID_MARGIN + 60
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hashiwokakero - Puentes Japoneses")
        self.font = pygame.font.SysFont('Arial', FONT_SIZE, bold=True)
        self.font_small = pygame.font.SysFont('Arial', FONT_SIZE_SMALL)
        self.message = ""
        self.message_color = INFO_COLOR
        self.message_timer = 0

    def load_board(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
            dimensions = lines[0].strip().split(',')
            self.rows = int(dimensions[0])
            self.cols = int(dimensions[1])
            self.board = []
            for i in range(1, self.rows + 1):
                row = [int(char) for char in lines[i].strip()]
                self.board.append(row)

    def draw_board(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Dibujar título y estado
        title = self.font_small.render("HASHIWOKAKERO", True, INFO_COLOR)
        self.screen.blit(title, (20, 15))

        status = self.font_small.render("Clic izquierdo: conectar | Clic dererecho: eliminar | ESC: reiniciar", True, INFO_COLOR)
        self.screen.blit(status, (20, 40))

        # Dibujar cuadrícula con líneas más sutiles
        for row in range(self.rows + 1):
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (GRID_MARGIN, GRID_MARGIN + row * CELL_SIZE),
                (GRID_MARGIN + self.cols * CELL_SIZE, GRID_MARGIN + row * CELL_SIZE),
                1
            )
        for col in range(self.cols + 1):
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN),
                (GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN + self.rows * CELL_SIZE),
                1
            )

        # Dibujar puentes
        for bridge in self.bridges:
            start_row, start_col = bridge[0]
            end_row, end_col = bridge[1]
            count = bridge[2]

            start_x = GRID_MARGIN + start_col * CELL_SIZE + CELL_SIZE // 2
            start_y = GRID_MARGIN + start_row * CELL_SIZE + CELL_SIZE // 2
            end_x = GRID_MARGIN + end_col * CELL_SIZE + CELL_SIZE // 2
            end_y = GRID_MARGIN + end_row * CELL_SIZE + CELL_SIZE // 2

            if start_row == end_row:  # Horizontal
                if count == 1:
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x, start_y), (end_x, end_y), 5)
                else:
                    offset = 7
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x, start_y - offset), (end_x, end_y - offset), 5)
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x, start_y + offset), (end_x, end_y + offset), 5)
            else:  # Vertical
                if count == 1:
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x, start_y), (end_x, end_y), 5)
                else:
                    offset = 7
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x - offset, start_y), (end_x - offset, end_y), 5)
                    pygame.draw.line(self.screen, BRIDGE_COLOR, (start_x + offset, start_y), (end_x + offset, end_y), 5)

        # Dibujar islas
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] > 0:
                    x = GRID_MARGIN + col * CELL_SIZE + CELL_SIZE // 2
                    y = GRID_MARGIN + row * CELL_SIZE + CELL_SIZE // 2
                    radius = CELL_SIZE // 3

                    # Sombra
                    pygame.draw.circle(self.screen, (150, 150, 150), (x + 2, y + 2), radius)

                    # Círculo de la isla
                    pygame.draw.circle(self.screen, ISLAND_COLOR, (x, y), radius)
                    pygame.draw.circle(self.screen, ISLAND_BORDER, (x, y), radius, 3)

                    # Resaltar isla seleccionada
                    if self.selected_island == (row, col):
                        pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y), radius + 5, 4)

                    # Determinar color del número según estado
                    current = self.count_bridges_for_island(row, col)
                    required = self.board[row][col]
                    if current == required:
                        num_color = SUCCESS_COLOR
                    elif current > required:
                        num_color = ERROR_COLOR
                    else:
                        num_color = TEXT_COLOR

                    # Número
                    num_text = self.font.render(str(self.board[row][col]), True, num_color)
                    text_rect = num_text.get_rect(center=(x, y))
                    self.screen.blit(num_text, text_rect)

        # Dibujar mensaje temporal
        if self.message and self.message_timer > 0:
            msg_surface = self.font_small.render(self.message, True, self.message_color)
            msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, msg_rect.inflate(20, 10))
            self.screen.blit(msg_surface, msg_rect)
            self.message_timer -= 1

        # Verificar si el juego está completo
        if self.check_victory():
            victory_text = self.font.render("¡JUEGO COMPLETADO!", True, SUCCESS_COLOR)
            victory_rect = victory_text.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, victory_rect.inflate(30, 15))
            pygame.draw.rect(self.screen, SUCCESS_COLOR, victory_rect.inflate(30, 15), 3)
            self.screen.blit(victory_text, victory_rect)

    def count_bridges_for_island(self, row, col):
        count = 0
        for bridge in self.bridges:
            if bridge[0] == (row, col) or bridge[1] == (row, col):
                count += bridge[2]
        return count

    def check_victory(self):
        # Verificar que todas las islas tengan el número correcto de puentes
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] > 0:
                    if self.count_bridges_for_island(row, col) != self.board[row][col]:
                        return False
        # Verificar conectividad (solo verifica que hay puentes)
        return len(self.bridges) > 0

    def show_message(self, text, color=INFO_COLOR, duration=60):
        self.message = text
        self.message_color = color
        self.message_timer = duration

    def get_island_at_pos(self, pos):
        x, y = pos
        if (GRID_MARGIN <= x < GRID_MARGIN + self.cols * CELL_SIZE and
                GRID_MARGIN <= y < GRID_MARGIN + self.rows * CELL_SIZE):
            col = (x - GRID_MARGIN) // CELL_SIZE
            row = (y - GRID_MARGIN) // CELL_SIZE
            if 0 <= row < self.rows and 0 <= col < self.cols and self.board[row][col] > 0:
                return (row, col)
        return None

    def can_add_bridge(self, start, end):
        if start == end:
            return False, "No puedes conectar una isla consigo misma"

        if start[0] != end[0] and start[1] != end[1]:
            return False, "Los puentes deben ser horizontales o verticales"

        # Verificar islas intermedias
        if start[0] == end[0]:  # Horizontal
            min_col = min(start[1], end[1])
            max_col = max(start[1], end[1])
            for col in range(min_col + 1, max_col):
                if self.board[start[0]][col] > 0:
                    return False, "Hay una isla en el camino"
        else:  # Vertical
            min_row = min(start[0], end[0])
            max_row = max(start[0], end[0])
            for row in range(min_row + 1, max_row):
                if self.board[row][start[1]] > 0:
                    return False, "Hay una isla en el camino"

        # Verificar cruce de puentes
        for bridge in self.bridges:
            if self.bridges_cross((start, end), (bridge[0], bridge[1])):
                return False, "Los puentes no pueden cruzarse"

        # Verificar límite de 2 puentes
        for bridge in self.bridges:
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                if bridge[2] >= 2:
                    return False, "Ya hay 2 puentes entre estas islas"

        # Verificar que no exceda el límite de la isla
        start_current = self.count_bridges_for_island(start[0], start[1])
        end_current = self.count_bridges_for_island(end[0], end[1])
        if start_current >= self.board[start[0]][start[1]]:
            return False, f"La isla {self.board[start[0]][start[1]]} ya tiene todos sus puentes"
        if end_current >= self.board[end[0]][end[1]]:
            return False, f"La isla destino ya tiene todos sus puentes"

        return True, "OK"

    def bridges_cross(self, bridge1, bridge2):
        # Verificar si dos puentes se cruzan
        s1, e1 = bridge1
        s2, e2 = bridge2

        # Si comparten un extremo, no se cruzan
        if s1 == s2 or s1 == e2 or e1 == s2 or e1 == e2:
            return False

        # Uno horizontal y otro vertical
        if s1[0] == e1[0] and s2[1] == e2[1]:  # bridge1 horizontal, bridge2 vertical
            h_row = s1[0]
            h_col_min, h_col_max = min(s1[1], e1[1]), max(s1[1], e1[1])
            v_col = s2[1]
            v_row_min, v_row_max = min(s2[0], e2[0]), max(s2[0], e2[0])
            return (v_row_min < h_row < v_row_max) and (h_col_min < v_col < h_col_max)

        if s1[1] == e1[1] and s2[0] == e2[0]:  # bridge1 vertical, bridge2 horizontal
            v_col = s1[1]
            v_row_min, v_row_max = min(s1[0], e1[0]), max(s1[0], e1[0])
            h_row = s2[0]
            h_col_min, h_col_max = min(s2[1], e2[1]), max(s2[1], e2[1])
            return (v_row_min < h_row < v_row_max) and (h_col_min < v_col < h_col_max)

        return False

    def add_bridge(self, start, end):
        for i, bridge in enumerate(self.bridges):
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                self.bridges[i] = (bridge[0], bridge[1], bridge[2] + 1)
                self.show_message("Puente añadido", SUCCESS_COLOR)
                return
        self.bridges.append((start, end, 1))
        self.show_message("Nuevo puente creado", SUCCESS_COLOR)

    def remove_bridge(self, start, end):
        for i, bridge in enumerate(self.bridges):
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                if bridge[2] > 1:
                    self.bridges[i] = (bridge[0], bridge[1], bridge[2] - 1)
                    self.show_message("Puente reducido", INFO_COLOR)
                else:
                    self.bridges.pop(i)
                    self.show_message("Puente eliminado", INFO_COLOR)
                return
        self.show_message("No hay puente para eliminar", ERROR_COLOR)

    def reset_game(self):
        self.bridges = []
        self.selected_island = None
        self.show_message("Juego reiniciado", INFO_COLOR)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset_game()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic izquierdo
                        island_pos = self.get_island_at_pos(event.pos)
                        if island_pos:
                            if self.selected_island is None:
                                self.selected_island = island_pos
                                self.show_message("Isla seleccionada, elige la siguiente", INFO_COLOR)
                            else:
                                can_add, message = self.can_add_bridge(self.selected_island, island_pos)
                                if can_add:
                                    self.add_bridge(self.selected_island, island_pos)
                                else:
                                    self.show_message(message, ERROR_COLOR)
                                self.selected_island = None

                    elif event.button == 3:  # Clic derecho
                        island_pos = self.get_island_at_pos(event.pos)
                        if island_pos:
                            if self.selected_island is None:
                                self.selected_island = island_pos
                                self.show_message("Selecciona la otra isla para eliminar puente", INFO_COLOR)
                            else:
                                self.remove_bridge(self.selected_island, island_pos)
                                self.selected_island = None

            self.draw_board()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    try:
        game = HashiwokakeroGame("board.txt")
        game.run()
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'board.txt'")
        print("Por favor, crea un archivo 'board.txt' con el formato correcto:")
        print("Primera línea: filas,columnas")
        print("Siguientes líneas: matriz del tablero")
        input("Presiona Enter para salir...")