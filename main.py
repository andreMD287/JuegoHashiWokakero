import pygame
import sys
from collections import deque

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


class GameState:
    """Clase que maneja el estado del juego (tablero y puentes)"""

    def __init__(self, filename):
        self.load_board(filename)
        self.bridges = []  # Lista de puentes: (start_pos, end_pos, count)

    def load_board(self, filename):
        """Carga el tablero desde un archivo"""
        with open(filename, 'r') as f:
            lines = f.readlines()
            dimensions = lines[0].strip().split(',')
            self.rows = int(dimensions[0])
            self.cols = int(dimensions[1])
            self.board = []
            for i in range(1, self.rows + 1):
                row = [int(char) for char in lines[i].strip()]
                self.board.append(row)

    def get_islands(self):
        """Retorna lista de todas las islas (row, col, value)"""
        islands = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] > 0:
                    islands.append((row, col, self.board[row][col]))
        return islands

    def count_bridges_for_island(self, row, col):
        """Cuenta puentes conectados a una isla"""
        count = 0
        for bridge in self.bridges:
            if bridge[0] == (row, col) or bridge[1] == (row, col):
                count += bridge[2]
        return count

    def get_bridge_between(self, start, end):
        """Obtiene el puente entre dos islas (si existe)"""
        for bridge in self.bridges:
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                return bridge
        return None

    def can_add_bridge(self, start, end):
        """Verifica si se puede agregar un puente entre dos islas"""
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
        existing_bridge = self.get_bridge_between(start, end)
        if existing_bridge and existing_bridge[2] >= 2:
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
        """Verifica si dos puentes se cruzan"""
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
        """Agrega un puente entre dos islas"""
        for i, bridge in enumerate(self.bridges):
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                self.bridges[i] = (bridge[0], bridge[1], bridge[2] + 1)
                return True
        self.bridges.append((start, end, 1))
        return True

    def remove_bridge(self, start, end):
        """Elimina un puente entre dos islas"""
        for i, bridge in enumerate(self.bridges):
            if (bridge[0] == start and bridge[1] == end) or (bridge[0] == end and bridge[1] == start):
                if bridge[2] > 1:
                    self.bridges[i] = (bridge[0], bridge[1], bridge[2] - 1)
                else:
                    self.bridges.pop(i)
                return True
        return False

    def get_neighbors(self, island_pos):
        """Obtiene las islas vecinas (en línea recta sin obstáculos)"""
        row, col = island_pos
        neighbors = []

        # Buscar hacia arriba
        for r in range(row - 1, -1, -1):
            if self.board[r][col] > 0:
                neighbors.append((r, col))
                break

        # Buscar hacia abajo
        for r in range(row + 1, self.rows):
            if self.board[r][col] > 0:
                neighbors.append((r, col))
                break

        # Buscar hacia la izquierda
        for c in range(col - 1, -1, -1):
            if self.board[row][c] > 0:
                neighbors.append((row, c))
                break

        # Buscar hacia la derecha
        for c in range(col + 1, self.cols):
            if self.board[row][c] > 0:
                neighbors.append((row, c))
                break

        return neighbors

    def check_connectivity(self):
        """Verifica que todas las islas estén conectadas mediante puentes"""
        islands = self.get_islands()
        if not islands:
            return True

        if len(self.bridges) == 0:
            return False

        # Construir grafo de adyacencia basado en puentes existentes
        graph = {(island[0], island[1]): [] for island in islands}

        for bridge in self.bridges:
            start, end = bridge[0], bridge[1]
            # Solo agregar si ambas islas existen en el grafo
            if start in graph and end in graph:
                if end not in graph[start]:
                    graph[start].append(end)
                if start not in graph[end]:
                    graph[end].append(start)

        # BFS desde la primera isla
        start_island = (islands[0][0], islands[0][1])
        visited = set()
        queue = deque([start_island])
        visited.add(start_island)

        while queue:
            current = queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Verificar que todas las islas fueron visitadas
        all_island_positions = {(island[0], island[1]) for island in islands}
        is_connected = visited == all_island_positions

        if not is_connected:
            print(f"Conectividad fallida: {len(visited)}/{len(all_island_positions)} islas conectadas")
            print(f"Islas aisladas: {all_island_positions - visited}")

        return is_connected

    def check_victory(self):
        """Verifica si el juego está completo"""
        # Verificar que todas las islas tengan el número correcto de puentes
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] > 0:
                    current = self.count_bridges_for_island(row, col)
                    required = self.board[row][col]
                    if current != required:
                        return False

        # Verificar que haya puentes
        if len(self.bridges) == 0:
            return False

        # Verificar conectividad (NO debe haber islas aisladas)
        return self.check_connectivity()

    def reset(self):
        """Reinicia el estado del juego"""
        self.bridges = []

    def copy(self):
        """Crea una copia del estado del juego"""
        new_state = GameState.__new__(GameState)
        new_state.rows = self.rows
        new_state.cols = self.cols
        new_state.board = [row[:] for row in self.board]
        new_state.bridges = [bridge for bridge in self.bridges]
        return new_state


class GameRenderer:
    """Clase que maneja el renderizado del juego"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.screen_width = game_state.cols * CELL_SIZE + 2 * GRID_MARGIN
        self.screen_height = game_state.rows * CELL_SIZE + 2 * GRID_MARGIN + 60
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hashiwokakero - Puentes Japoneses")
        self.font = pygame.font.SysFont('Arial', FONT_SIZE, bold=True)
        self.font_small = pygame.font.SysFont('Arial', FONT_SIZE_SMALL)
        self.message = ""
        self.message_color = INFO_COLOR
        self.message_timer = 0
        self.selected_island = None

    def show_message(self, text, color=INFO_COLOR, duration=60):
        """Muestra un mensaje temporal"""
        self.message = text
        self.message_color = color
        self.message_timer = duration

    def draw(self):
        """Dibuja todo el juego"""
        self.screen.fill(BACKGROUND_COLOR)

        # Dibujar título y estado
        title = self.font_small.render("HASHIWOKAKERO", True, INFO_COLOR)
        self.screen.blit(title, (20, 15))

        status = self.font_small.render(
            "Clic izq: conectar | Clic der: eliminar | ESC: reiniciar | ESPACIO: resolver | +/-: velocidad", True,
            INFO_COLOR)
        self.screen.blit(status, (20, 40))

        # Dibujar cuadrícula
        self._draw_grid()

        # Dibujar puentes
        self._draw_bridges()

        # Dibujar islas
        self._draw_islands()

        # Dibujar mensaje temporal
        if self.message and self.message_timer > 0:
            msg_surface = self.font_small.render(self.message, True, self.message_color)
            msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, msg_rect.inflate(20, 10))
            self.screen.blit(msg_surface, msg_rect)
            self.message_timer -= 1

        # Verificar victoria
        if self.game_state.check_victory():
            victory_text = self.font.render("¡JUEGO COMPLETADO!", True, SUCCESS_COLOR)
            victory_rect = victory_text.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, victory_rect.inflate(30, 15))
            pygame.draw.rect(self.screen, SUCCESS_COLOR, victory_rect.inflate(30, 15), 3)
            self.screen.blit(victory_text, victory_rect)
        elif self._check_all_islands_complete() and not self.game_state.check_connectivity():
            # Todas las islas tienen sus puentes pero hay islas aisladas
            warning_text = self.font_small.render("¡Hay islas aisladas!", True, ERROR_COLOR)
            warning_rect = warning_text.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, warning_rect.inflate(20, 10))
            self.screen.blit(warning_text, warning_rect)

    def _check_all_islands_complete(self):
        """Verifica si todas las islas tienen el número correcto de puentes"""
        for row in range(self.game_state.rows):
            for col in range(self.game_state.cols):
                if self.game_state.board[row][col] > 0:
                    current = self.game_state.count_bridges_for_island(row, col)
                    required = self.game_state.board[row][col]
                    if current != required:
                        return False
        return True

    def _draw_grid(self):
        """Dibuja la cuadrícula"""
        for row in range(self.game_state.rows + 1):
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (GRID_MARGIN, GRID_MARGIN + row * CELL_SIZE),
                (GRID_MARGIN + self.game_state.cols * CELL_SIZE, GRID_MARGIN + row * CELL_SIZE),
                1
            )
        for col in range(self.game_state.cols + 1):
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN),
                (GRID_MARGIN + col * CELL_SIZE, GRID_MARGIN + self.game_state.rows * CELL_SIZE),
                1
            )

    def _draw_bridges(self):
        """Dibuja los puentes"""
        for bridge in self.game_state.bridges:
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

    def _draw_islands(self):
        """Dibuja las islas"""
        for row in range(self.game_state.rows):
            for col in range(self.game_state.cols):
                if self.game_state.board[row][col] > 0:
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
                    current = self.game_state.count_bridges_for_island(row, col)
                    required = self.game_state.board[row][col]
                    if current == required:
                        num_color = SUCCESS_COLOR
                    elif current > required:
                        num_color = ERROR_COLOR
                    else:
                        num_color = TEXT_COLOR

                    # Número
                    num_text = self.font.render(str(self.game_state.board[row][col]), True, num_color)
                    text_rect = num_text.get_rect(center=(x, y))
                    self.screen.blit(num_text, text_rect)

    def get_island_at_pos(self, pos):
        """Obtiene la isla en una posición de pantalla"""
        x, y = pos
        if (GRID_MARGIN <= x < GRID_MARGIN + self.game_state.cols * CELL_SIZE and
                GRID_MARGIN <= y < GRID_MARGIN + self.game_state.rows * CELL_SIZE):
            col = (x - GRID_MARGIN) // CELL_SIZE
            row = (y - GRID_MARGIN) // CELL_SIZE
            if 0 <= row < self.game_state.rows and 0 <= col < self.game_state.cols and self.game_state.board[row][
                col] > 0:
                return (row, col)
        return None


class HumanPlayer:
    """Jugador humano que interactúa con el mouse"""

    def __init__(self, game_state, renderer):
        self.game_state = game_state
        self.renderer = renderer

    def handle_event(self, event):
        """Maneja eventos de entrada del jugador"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic izquierdo
                island_pos = self.renderer.get_island_at_pos(event.pos)
                if island_pos:
                    if self.renderer.selected_island is None:
                        self.renderer.selected_island = island_pos
                        self.renderer.show_message("Isla seleccionada, elige la siguiente", INFO_COLOR)
                    else:
                        can_add, message = self.game_state.can_add_bridge(self.renderer.selected_island, island_pos)
                        if can_add:
                            self.game_state.add_bridge(self.renderer.selected_island, island_pos)
                            self.renderer.show_message("Puente añadido", SUCCESS_COLOR)
                        else:
                            self.renderer.show_message(message, ERROR_COLOR)
                        self.renderer.selected_island = None

            elif event.button == 3:  # Clic derecho
                island_pos = self.renderer.get_island_at_pos(event.pos)
                if island_pos:
                    if self.renderer.selected_island is None:
                        self.renderer.selected_island = island_pos
                        self.renderer.show_message("Selecciona la otra isla para eliminar puente", INFO_COLOR)
                    else:
                        if self.game_state.remove_bridge(self.renderer.selected_island, island_pos):
                            self.renderer.show_message("Puente eliminado", INFO_COLOR)
                        else:
                            self.renderer.show_message("No hay puente para eliminar", ERROR_COLOR)
                        self.renderer.selected_island = None


class AutoPlayer:
    """Jugador automático que resuelve el juego usando backtracking con heurísticas"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.solution_steps = []
        self.solving = False
        self.step_index = 0
        self.iterations = 0
        self.max_iterations = 500000  # Límite de seguridad aumentado

    def solve(self):
        """Resuelve el juego y guarda los pasos de la solución"""
        print("Iniciando resolución automática...")
        self.solution_steps = []  # Limpiar pasos anteriores
        self.iterations = 0

        # Guardar estado inicial
        initial_bridges = [bridge for bridge in self.game_state.bridges]

        # Aplicar heurísticas simples primero
        print("Aplicando heurísticas...")
        self._apply_forced_moves()

        print(f"Después de heurísticas: {len(self.game_state.bridges)} puentes")

        # Usar backtracking para completar
        print("Iniciando backtracking...")
        if self._backtrack():
            print(f"¡Solución encontrada con {len(self.solution_steps)} pasos!")
            print(f"Iteraciones del backtracking: {self.iterations}")

            # Verificar que la solución es válida
            if self.game_state.check_victory():
                print("✓ Solución validada correctamente")
                print(f"✓ Total de puentes: {len(self.game_state.bridges)}")
                print(f"✓ Conectividad verificada")
                return True
            else:
                print("✗ ADVERTENCIA: La solución no es válida")
                is_connected = self.game_state.check_connectivity()
                print(f"  - Conectividad: {is_connected}")
                # Restaurar estado inicial
                self.game_state.bridges = initial_bridges
                return False
        else:
            print(f"✗ No se encontró solución (iteraciones: {self.iterations})")
            # Restaurar estado inicial
            self.game_state.bridges = initial_bridges
            return False

    def _apply_forced_moves(self):
        """Aplica movimientos forzados (heurísticas greedy)"""
        changed = True
        iterations = 0
        max_iterations = 100

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            islands = self.game_state.get_islands()

            for row, col, required in islands:
                current = self.game_state.count_bridges_for_island(row, col)
                remaining = required - current

                if remaining <= 0:
                    continue

                neighbors = self.game_state.get_neighbors((row, col))
                valid_neighbors = []

                for neighbor in neighbors:
                    can_add, _ = self.game_state.can_add_bridge((row, col), neighbor)
                    if can_add:
                        # Verificar cuántos puentes más se pueden agregar
                        existing = self.game_state.get_bridge_between((row, col), neighbor)
                        if existing:
                            if existing[2] < 2:
                                valid_neighbors.append(neighbor)
                        else:
                            valid_neighbors.append(neighbor)

                if len(valid_neighbors) == 0:
                    continue

                # Heurística 1: Si solo queda un vecino válido, conectar todo ahí
                if len(valid_neighbors) == 1:
                    neighbor = valid_neighbors[0]
                    neighbor_current = self.game_state.count_bridges_for_island(neighbor[0], neighbor[1])
                    neighbor_required = self.game_state.board[neighbor[0]][neighbor[1]]
                    neighbor_remaining = neighbor_required - neighbor_current

                    bridges_to_add = min(remaining, neighbor_remaining, 2)
                    existing = self.game_state.get_bridge_between((row, col), neighbor)
                    if existing:
                        bridges_to_add = min(bridges_to_add, 2 - existing[2])

                    for _ in range(bridges_to_add):
                        can_add, _ = self.game_state.can_add_bridge((row, col), neighbor)
                        if can_add:
                            self.game_state.add_bridge((row, col), neighbor)
                            self.solution_steps.append(((row, col), neighbor, "add"))
                            changed = True

                # Heurística 2: Si remaining == suma máxima posible de puentes a vecinos
                total_capacity = 0
                for neighbor in valid_neighbors:
                    existing = self.game_state.get_bridge_between((row, col), neighbor)
                    if existing:
                        capacity = 2 - existing[2]
                    else:
                        capacity = 2

                    neighbor_current = self.game_state.count_bridges_for_island(neighbor[0], neighbor[1])
                    neighbor_required = self.game_state.board[neighbor[0]][neighbor[1]]
                    neighbor_remaining = neighbor_required - neighbor_current

                    capacity = min(capacity, neighbor_remaining)
                    total_capacity += capacity

                # Si el remaining es igual a la capacidad total, usar toda la capacidad
                if total_capacity == remaining and remaining > 0:
                    for neighbor in valid_neighbors:
                        existing = self.game_state.get_bridge_between((row, col), neighbor)
                        if existing:
                            bridges_needed = 2 - existing[2]
                        else:
                            bridges_needed = 2

                        neighbor_current = self.game_state.count_bridges_for_island(neighbor[0], neighbor[1])
                        neighbor_required = self.game_state.board[neighbor[0]][neighbor[1]]
                        neighbor_remaining = neighbor_required - neighbor_current

                        bridges_needed = min(bridges_needed, neighbor_remaining)

                        for _ in range(bridges_needed):
                            can_add, _ = self.game_state.can_add_bridge((row, col), neighbor)
                            if can_add:
                                self.game_state.add_bridge((row, col), neighbor)
                                self.solution_steps.append(((row, col), neighbor, "add"))
                                changed = True

    def _backtrack(self):
        """Backtracking para encontrar solución"""
        self.iterations += 1

        # Límite de seguridad
        if self.iterations > self.max_iterations:
            print(f"Límite de iteraciones alcanzado ({self.max_iterations})")
            return False

        # Mostrar progreso cada 10000 iteraciones
        if self.iterations % 10000 == 0:
            print(f"  Iteración {self.iterations}, puentes actuales: {len(self.game_state.bridges)}")

        # Verificar si ya está resuelto
        if self.game_state.check_victory():
            return True

        # Encontrar isla con puentes incompletos
        islands = self.game_state.get_islands()

        # Verificar si alguna isla excedió su limite (poda temprana)
        for row, col, required in islands:
            current = self.game_state.count_bridges_for_island(row, col)
            if current > required:
                return False

        # Ordenar por restricción (menos opciones primero)
        islands_sorted = []
        for row, col, required in islands:
            current = self.game_state.count_bridges_for_island(row, col)
            if current < required:
                neighbors = self.game_state.get_neighbors((row, col))
                valid_neighbors = []
                for n in neighbors:
                    # Verificar que el vecino no esté completo
                    neighbor_current = self.game_state.count_bridges_for_island(n[0], n[1])
                    neighbor_required = self.game_state.board[n[0]][n[1]]
                    if neighbor_current < neighbor_required:
                        can_add, _ = self.game_state.can_add_bridge((row, col), n)
                        if can_add:
                            valid_neighbors.append(n)

                # Si una isla necesita puentes pero no tiene vecinos válidos, es imposible
                remaining = required - current
                if len(valid_neighbors) == 0 and remaining > 0:
                    return False

                islands_sorted.append((row, col, required, current, len(valid_neighbors), valid_neighbors, remaining))

        # Si no hay islas incompletas, verificar solución completa
        if not islands_sorted:
            return self.game_state.check_victory()

        # Ordenar por número de opciones válidas (MRV) y luego por puentes restantes
        islands_sorted.sort(key=lambda x: (x[4], -x[6]))

        row, col, required, current, _, valid_neighbors, remaining = islands_sorted[0]

        # Intentar conectar con cada vecino válido
        for neighbor in valid_neighbors:
            neighbor_row, neighbor_col = neighbor
            neighbor_required = self.game_state.board[neighbor_row][neighbor_col]
            neighbor_current = self.game_state.count_bridges_for_island(neighbor_row, neighbor_col)
            neighbor_remaining = neighbor_required - neighbor_current

            if neighbor_remaining <= 0:
                continue

            # Determinar cuántos puentes intentar (1 o 2)
            max_bridges = min(remaining, neighbor_remaining)

            # Verificar cuántos puentes ya existen entre estas islas
            existing_bridge = self.game_state.get_bridge_between((row, col), neighbor)
            if existing_bridge:
                existing_count = existing_bridge[2]
                max_bridges = min(max_bridges, 2 - existing_count)
            else:
                max_bridges = min(max_bridges, 2)

            if max_bridges <= 0:
                continue

            # Intentar agregar puentes (primero 1, luego 2 para explorar más rápido)
            for bridges_to_add in range(1, max_bridges + 1):
                success = True
                added_count = 0

                # Verificar y agregar puentes
                for _ in range(bridges_to_add):
                    can_add, _ = self.game_state.can_add_bridge((row, col), neighbor)
                    if not can_add:
                        success = False
                        break
                    self.game_state.add_bridge((row, col), neighbor)
                    self.solution_steps.append(((row, col), neighbor, "add"))
                    added_count += 1

                if not success:
                    # Deshacer puentes agregados parcialmente
                    for _ in range(added_count):
                        self.game_state.remove_bridge((row, col), neighbor)
                        if self.solution_steps and self.solution_steps[-1][2] == "add":
                            self.solution_steps.pop()
                    continue

                # Recursión
                if self._backtrack():
                    return True

                # Deshacer (backtrack)
                for _ in range(bridges_to_add):
                    self.game_state.remove_bridge((row, col), neighbor)
                    if self.solution_steps and self.solution_steps[-1][2] == "add":
                        self.solution_steps.pop()

        return False

    def start_visualization(self):
        """Inicia la visualización paso a paso de la solución"""
        self.solving = True
        self.step_index = 0
        self.game_state.reset()

    def next_step(self):
        """Ejecuta el siguiente paso de la solución"""
        if self.step_index < len(self.solution_steps):
            start, end, action = self.solution_steps[self.step_index]
            if action == "add":
                self.game_state.add_bridge(start, end)
            self.step_index += 1
            return True
        return False


class HashiwokakeroGame:
    """Clase principal que coordina el juego"""

    def __init__(self, filename, auto_mode=False):
        self.game_state = GameState(filename)
        self.renderer = GameRenderer(self.game_state)
        self.player = HumanPlayer(self.game_state, self.renderer)
        self.auto_player = AutoPlayer(self.game_state)
        self.auto_mode = auto_mode
        self.auto_step_timer = 0
        self.auto_step_delay = 5  # frames entre pasos (ajustable con +/-)
        self.show_instructions = True

    def reset_game(self):
        """Reinicia el juego"""
        self.game_state.reset()
        self.renderer.selected_island = None
        self.renderer.show_message("Juego reiniciado", INFO_COLOR)
        self.auto_mode = False

    def start_auto_solve(self):
        """Inicia la resolución automática"""
        self.game_state.reset()
        self.renderer.selected_island = None
        if self.auto_player.solve():
            self.auto_player.start_visualization()
            self.auto_mode = True
            self.renderer.show_message("Reproduciendo solución...", SUCCESS_COLOR, 120)
        else:
            self.renderer.show_message("No se pudo resolver el puzzle", ERROR_COLOR, 120)

    def run(self):
        """Bucle principal del juego"""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset_game()
                    elif event.key == pygame.K_SPACE:
                        # Presionar ESPACIO para resolver automáticamente
                        self.start_auto_solve()
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        # Aumentar velocidad
                        self.auto_step_delay = max(1, self.auto_step_delay - 2)
                        self.renderer.show_message(f"Velocidad: {self.auto_step_delay} frames/paso", INFO_COLOR, 60)
                    elif event.key == pygame.K_MINUS:
                        # Disminuir velocidad
                        self.auto_step_delay = min(60, self.auto_step_delay + 2)
                        self.renderer.show_message(f"Velocidad: {self.auto_step_delay} frames/paso", INFO_COLOR, 60)
                else:
                    if not self.auto_mode:
                        self.player.handle_event(event)

            # Modo automático: ejecutar siguiente paso
            if self.auto_mode:
                self.auto_step_timer += 1
                if self.auto_step_timer >= self.auto_step_delay:
                    self.auto_step_timer = 0
                    if not self.auto_player.next_step():
                        self.auto_mode = False
                        if self.game_state.check_victory():
                            self.renderer.show_message("¡Solución completada!", SUCCESS_COLOR, 180)

            self.renderer.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    try:
        game = HashiwokakeroGame("prueba.txt")
        game.run()
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'board.txt'")
        print("Por favor, crea un archivo 'board.txt' con el formato correcto:")
        print("Primera línea: filas,columnas")
        print("Siguientes líneas: matriz del tablero")
        input("Presiona Enter para salir...")