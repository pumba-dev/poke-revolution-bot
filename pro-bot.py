import pyautogui
import cv2
import numpy as np
import os
import time
import pytesseract
import sys
import pygetwindow as gw
from pywinauto import Application
import keyboard
import pyperclip
import threading

## META DATA - Não mexer ##
stop_execution = False  # Flag para encerrar a execução do bot
GAME_WINDOW = "PROClient"  # Nome do processo do jogo
LOG_IMG_COUNT = 1  # Contador de imagens salvas
MAX_LOG_COUNT = 10  # Quantidade máxima de imagens salvas
BATTLE_COUNT = 0  # Contador de batalhas
RARE_CATCH_COUNT = 0  # Contador de pokemon raros capturados
POKE_CATCH_COUNT = []  # Lista de pokemons capturados
WAITING_TIME = 3.25  # Tempo de espera antes de verificar se o pokemon é capturável
TRADE_MSG_TIME = 10  # Enviar mensagem no trade a cada X batalhas
WALK_TIME = 0.5  # Tempo de caminhar para um lado

## PARAMETROS DE CONFIGURACAO ##
# |- Lista de pokebolas para captura
# |- A ordem de prioridade é a ordem da lista
# |- Deixe a pokebola visível na barra de ação do jogo.
CATCH_POKEBALL = "ultraball"
# |- Lista de pokemons para captura
CATCH_POKE_LIST = [
    "Snivy",
    "Froakie",
    "Tepig",
    "Summer",
    "Shiny",
]
# |- Mensagem para enviar no chat
# |- Selecione, no jogo, o chat que deseja enviar a mensagem
# |- Caso não queira enviar mensagem, deixar vazio (0 ou None)
# TRADE_MESSAGE = "want to sell # epic [Poke94957828] 3x 31 # Summer protean (bb) [Poke95096645] # send u offer pm"
# TRADE_MESSAGE = "BUY BLACK MEDALLION | 170K | PM ME"ad
TRADE_MESSAGE = None


class Pokemon:
    def __init__(self, nome, quantidade):
        self.name = nome
        self.quantity = quantidade

    def __repr__(self):
        return f"{self.name}: [{self.quantity}]"


def handle_close_app(e=None):
    sys.stdout.write("\n\n🔴 Em instantes o bot será encerrado 🔴\n\n")
    sys.stdout.flush()
    global stop_execution
    stop_execution = True
    sys.exit(0)


def send_keys_to_process(keys):
    try:
        # Conectar ao aplicativo pelo nome do processo
        app = Application().connect(
            title_re=GAME_WINDOW, backend="win32", visible_only=False
        )

        # Selecionar a janela principal do aplicativo
        window = app.window(title_re=GAME_WINDOW)

        # Enviar comandos do teclado diretamente para a janela
        window.send_keystrokes(keys)

    except Exception as e:
        print(f"Erro ao enviar comandos para o processo: {e}")


def open_game_window():
    try:
        window = gw.getWindowsWithTitle(GAME_WINDOW)[0]
        if window.isMinimized:
            window.restore()
        window.activate()
    except IndexError:
        # print("Erro: Janela do jogo não encontrada.")
        return
    except gw.PyGetWindowException as e:
        # print(f"Erro ao ativar a janela do jogo: {e}")
        return


def click_at_position(x, y):
    pyautogui.moveTo(x, y)
    pyautogui.click()


def take_screenshot(size=None):
    open_game_window()

    screen_width, screen_height = pyautogui.size()
    if size:
        width, height = size
        left = (screen_width - width) // 2
        top = (screen_height - height) // 2
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
    else:
        screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_cv2 = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_cv2


def find_image_on_screen(image_path, threshold=0.8):
    script_dir = os.path.dirname(__file__)
    abs_image_path = os.path.join(script_dir, image_path)
    template = cv2.imread(abs_image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(
            f"Não foi possível encontrar o arquivo: {abs_image_path}"
        )
    screen = take_screenshot()
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val > threshold:
        w, h = template.shape[::-1]
        center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
        return center_x, center_y
    else:
        return None


def extract_text_on_battle(image):
    try:
        global LOG_IMG_COUNT
        base_dir = f"./logs/{LOG_IMG_COUNT}"

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        cv2.imwrite(f"./logs/{LOG_IMG_COUNT}/battle_image.png", image)

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f"./logs/{LOG_IMG_COUNT}/battle_gray_image.png", gray_image)

        _, processed_image = cv2.threshold(gray_image, 125, 255, cv2.THRESH_BINARY_INV)

        kernel = np.ones((1, 1), np.uint8)
        processed_image = cv2.dilate(processed_image, kernel, iterations=10)

        kernel = np.ones((1, 1), np.uint8)
        processed_image = cv2.erode(processed_image, kernel, iterations=10)

        cv2.imwrite(
            f"./logs/{LOG_IMG_COUNT}/battle_processed_image.png", processed_image
        )

        custom_config = r"--oem 3 --psm 6"
        extracted_text = pytesseract.image_to_string(
            processed_image, config=custom_config
        )

        with open(
            f"./logs/{LOG_IMG_COUNT}/battle_extracted_text.txt", "w", encoding="utf-8"
        ) as file:
            file.write(extracted_text.lower())
            file.flush()

        return extracted_text.lower()
    except Exception as e:
        print(f"Erro ao encontrar texto na tela: {e}")
        return False


def game_in_battle_mode():
    fightBtnPos = find_image_on_screen("./assets/icons/battle_icon.png")
    if fightBtnPos is not None:
        return True


def add_new_catched_poke(newPoke):
    global POKE_CATCH_COUNT
    for poke in POKE_CATCH_COUNT:
        if poke.name == newPoke:
            poke.quantity += 1
            return
    POKE_CATCH_COUNT.append(Pokemon(newPoke, 1))
    return


def enemy_pokemon_is_catchable():
    sys.stdout.write("Verificando se o wild pokemon é capturável 🔄\n")

    screen = take_screenshot(size=(800, 500))
    battleText = extract_text_on_battle(screen)

    if not battleText:
        sys.stdout.write(
            "[ERROR] Algo inexperado aconteceu ao extrair texto da imagem da batalha ❌\n"
        )
        sys.stdout.flush()
        return False

    for poke in CATCH_POKE_LIST:
        if poke.lower() in battleText.lower():
            sys.stdout.write(f"\rEncontrado {poke} para capturar ✅\n")
            sys.stdout.flush()

            add_new_catched_poke(poke)
            return poke

    sys.stdout.write("\rPokemon não está na lista para captura ❌\n")
    sys.stdout.flush()
    return False


def enemy_pokemon_is_rare():
    global RARE_CATCH_COUNT
    sys.stdout.write("Verificando se o wild pokemon é raro 🔄\n")

    rare_pokemon = find_image_on_screen("./assets/icons/rare_pokemon.png")
    if rare_pokemon:
        sys.stdout.flush()
        sys.stdout.write("\n🎉 POKEMON RARO ENCONTRADO!! ✅\n")
        RARE_CATCH_COUNT += 1
        return True
    else:
        sys.stdout.flush()
        sys.stdout.write("\rPokemon encontrado não é raro ❌\n")
        return False


def catch_wild_pokemon():
    global CATCH_POKEBALL
    sys.stdout.write("\nCapturando pokemon selvagem ⚪🔴\n")

    pokeball = find_image_on_screen(f"./assets/pokeballs/{CATCH_POKEBALL}.png", 0.95)
    if pokeball:
        in_battle = True
        while in_battle:
            time.sleep(0.25)
            click_at_position(*pokeball)
            in_battle = game_in_battle_mode()
        return True
    else:
        sys.stdout.write("[ERROR] Pokebola não encontrada ❌\n")
        handle_close_app()

    return False


def walk_until_start_battle():
    sys.stdout.write("\nIniciando loop de caminhada 🚶\n")
    sys.stdout.flush()
    while True:
        in_battle = game_in_battle_mode()
        if in_battle is not None:
            break
        global BATTLE_COUNT
        side1 = "a" if BATTLE_COUNT % np.random.randint(2, 3) == 0 else "d"
        side2 = "d" if BATTLE_COUNT % np.random.randint(2, 3) == 0 else "a"
        global WALK_TIME
        time1 = 0.2 + ((WALK_TIME - 0.2) * np.random.random())
        time2 = 0.2 + ((WALK_TIME - 0.2) * np.random.random())
        pyautogui.keyDown(side1)
        time.sleep(time1)
        pyautogui.keyUp(side1)
        pyautogui.keyDown(side2)
        time.sleep(time2)
        pyautogui.keyUp(side2)


def run_away_wild_battle():
    sys.stdout.write("\nTentando fugir da batalha 🚪\n")
    sys.stdout.flush()

    in_battle = game_in_battle_mode()
    while in_battle:
        time.sleep(0.3)
        pyautogui.press("4")
        in_battle = game_in_battle_mode()


def printCatchLog():
    global BATTLE_COUNT
    global RARE_CATCH_COUNT
    global POKE_CATCH_COUNT
    global BALL_USE_COUNT

    sys.stdout.write("\n\n\n📍 INICIANDO NOVO CICLO 📍\n\n")

    sys.stdout.write("💥 Batalhas iniciadas: ")
    if BATTLE_COUNT > 0:
        sys.stdout.write(str(BATTLE_COUNT) + "\n")
    else:
        sys.stdout.write("🅾️\n")

    sys.stdout.write("💎 Raros capturados: ")
    if RARE_CATCH_COUNT > 0:
        sys.stdout.write(str(RARE_CATCH_COUNT) + "\n")
    else:
        sys.stdout.write("🅾️\n")

    sys.stdout.write("🔴⚪️ Pokemons capturados: ")
    if len(POKE_CATCH_COUNT) > 0:
        sys.stdout.write("\n")
        for poke in POKE_CATCH_COUNT:
            sys.stdout.write(f"{poke}\n")
    else:
        sys.stdout.write("🅾️\n")


def sendTradeChatMessage():
    sys.stdout.write("\n📋 Mandando mensagem no Trade 🤝\n")

    open_game_window()

    global TRADE_MESSAGE
    pyperclip.copy(TRADE_MESSAGE)

    pyautogui.press("enter")

    pyautogui.keyDown("ctrl")
    pyautogui.press("v")
    pyautogui.keyUp("ctrl")

    pyautogui.press("enter")


if __name__ == "__main__":
    try:
        pyautogui.FAILSAFE = False
        keyboard.on_press_key("esc", handle_close_app)

        open_game_window()

        # LOOP PRINCIPAL
        while True:
            if stop_execution == True:
                sys.stdout.write("\n\n🔴 Encerrando aplicação 🔴\n\n")
                break

            printCatchLog()

            if TRADE_MESSAGE and BATTLE_COUNT % TRADE_MSG_TIME == 0:
                sendTradeChatMessage()

            in_battle = game_in_battle_mode()
            if not in_battle:
                walk_until_start_battle()

            BATTLE_COUNT += 1
            sys.stdout.write("\nUma batalha foi iniciada ⚔️\n")
            sys.stdout.flush()

            time.sleep(WAITING_TIME)

            if enemy_pokemon_is_catchable():
                catch_wild_pokemon()
            elif enemy_pokemon_is_rare():
                catch_wild_pokemon()
            else:
                run_away_wild_battle()

            LOG_IMG_COUNT += 1
            if LOG_IMG_COUNT > MAX_LOG_COUNT:
                LOG_IMG_COUNT = 1

    except KeyboardInterrupt:
        handle_close_app()
