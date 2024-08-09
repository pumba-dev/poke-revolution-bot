import pyautogui
import cv2
import numpy as np
import os
import time
import pytesseract
import sys

# Def catch list of pokemons
BATTLE_COUNT = 0
RARE_CATCH_COUNT = 0
POKE_CATCH_COUNT = []
POKEBALL_LIST = ["pokeball", "ultraball"]
CATCH_POKE_LIST = ["Froakie", "Summer", "Shiny", "Alolan", "Snivy", "Pikachu"]


def click_at_position(x, y):
    pyautogui.moveTo(x, y)
    pyautogui.click()


def take_screenshot(size=None):
    """
    Tira um screenshot da tela e retorna a imagem em formato que possa ser utilizado para fazer match.
    Se o parâmetro 'size' for fornecido, captura uma área de tamanho 'size' (largura, altura) a partir do centro da tela.
    """
    screen_width, screen_height = pyautogui.size()

    if size:
        width, height = size
        left = (screen_width - width) // 2
        top = (screen_height - height) // 2
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
    else:
        screenshot = pyautogui.screenshot()

    screenshot_np = np.array(screenshot)
    # Convertendo para o formato que o OpenCV pode trabalhar
    screenshot_cv2 = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_cv2


def find_image_on_screen(image_path):
    """
    Recebe o caminho de uma imagem PNG como parâmetro e procura essa imagem na tela.
    Retorna as coordenadas do centro da imagem encontrada.
    """
    # Obtém o diretório onde o script atual reside
    script_dir = os.path.dirname(__file__)
    # Constrói um caminho absoluto para o arquivo de imagem
    abs_image_path = os.path.join(script_dir, image_path)

    # Tenta carregar a imagem usando o caminho absoluto
    template = cv2.imread(abs_image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(
            f"Não foi possível encontrar o arquivo: {abs_image_path}"
        )

    # Captura a tela e converte para escala de cinza
    screen = take_screenshot()
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.8:  # Considerando um match bom se a correlação for maior que 80%
        w, h = template.shape[::-1]
        center_x, center_y = max_loc[0] + w // 2, max_loc[1] + h // 2
        return center_x, center_y
    else:
        return None


def find_text_on_screen(search_string, image):
    try:
        # Converte a imagem para escala de cinza
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Aplica um limiar (threshold) para binarizar a imagem
        _, processed_image = cv2.threshold(gray_image, 125, 255, cv2.THRESH_BINARY_INV)

        # Realiza OCR na imagem processada
        custom_config = r"--oem 3 --psm 6"
        extracted_text = pytesseract.image_to_string(
            processed_image, config=custom_config
        )

        # Salvar log
        with open("./logs/extracted_text.txt", "w", encoding="utf-8") as file:
            file.write(extracted_text.lower())
            file.flush()

        # Verifica se a string fornecida está presente no texto extraído
        return search_string.lower() in extracted_text.lower()
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
        if poke[0] == newPoke:
            poke_list = list(poke)
            poke_list[1] += 1
            poke = tuple(poke_list)
            return

    POKE_CATCH_COUNT.append((newPoke, 1))
    return


def enemy_pokemon_is_catchable():
    global POKE_CATCH_COUNT
    sys.stdout.write("Verificando se o wild pokemon é capturável 🔄\n")

    screen = take_screenshot(size=(800, 500))

    cv2.imwrite("./logs/screen.png", screen)

    for poke in CATCH_POKE_LIST:
        if find_text_on_screen(poke, screen):
            sys.stdout.flush()
            sys.stdout.write(f"\rEncontrado {poke} para capturar ✅\n")
            add_new_catched_poke(poke)
            return poke

    sys.stdout.flush()
    sys.stdout.write("\rPokemon não está na lista para captura ❌\n")
    return False


def enemy_pokemon_is_rare():
    global RARE_CATCH_COUNT
    sys.stdout.write("Verificando se o wild pokemon é raro 🔄\n")

    rare_pokemon = find_image_on_screen("./assets/icons/rare_pokemon.png")

    if rare_pokemon:
        sys.stdout.flush()
        sys.stdout.write("\rPOKEMON RARO ENCONTRADO ✅\n")
        RARE_CATCH_COUNT += 1
        return True
    else:
        sys.stdout.flush()
        sys.stdout.write("\rPokemon encontrado não é raro ❌\n")
        return False


def catch_wild_pokemon():
    sys.stdout.write("Capturando pokemon selvagem ⚪🔴\n")

    for pokeball in POKEBALL_LIST:
        pokeballPos = find_image_on_screen(f"./assets/pokeballs/{pokeball}.png")
        if pokeballPos:
            print("Item utilizado: " + pokeball)
            in_battle = True
            while in_battle:
                click_at_position(*pokeballPos)
                time.sleep(1)
                in_battle = game_in_battle_mode()
            return True

    return False


def walk_until_start_battle():
    sys.stdout.write("\nIniciando loop de caminhada 🚶\n")
    sys.stdout.flush()

    while True:
        in_battle = game_in_battle_mode()
        if in_battle is not None:
            break

        side1 = "a" if BATTLE_COUNT % 2 == 0 else "d"
        side2 = "d" if BATTLE_COUNT % 2 == 0 else "a"
        time1 = 0.3 + (0.5 * np.random.random())
        time2 = 0.3 + (0.5 * np.random.random())

        pyautogui.keyDown(side1)
        time.sleep(time1)
        pyautogui.keyUp(side1)

        pyautogui.keyDown(side2)
        time.sleep(time2)
        pyautogui.keyUp(side2)


def run_away_wild_battle():
    in_battle = game_in_battle_mode()
    while in_battle:
        sys.stdout.write("Tentando fugir da batalha 🚪\n")
        sys.stdout.flush()
        pyautogui.press("4")
        time.sleep(0.5)
        in_battle = game_in_battle_mode()


def printCatchLog():
    global BATTLE_COUNT
    global RARE_CATCH_COUNT

    sys.stdout.write("\n\n📍 INICIANDO NOVO CICLO 📍\n")
    sys.stdout.write("💥 Batalhas iniciadas: " + str(BATTLE_COUNT) + "\n")
    sys.stdout.write("💎 Pokemons raros capturados: " + str(RARE_CATCH_COUNT) + "\n")
    sys.stdout.write("🔴 Pokemons capturados ⚪️ \n")
    if len(POKE_CATCH_COUNT) == 0:
        sys.stdout.write("Nenhum 🅾️\n")
    else:
        for poke in POKE_CATCH_COUNT:
            sys.stdout.write(f"{poke[0]}: {poke[1]}\n")


if __name__ == "__main__":
    while True:
        printCatchLog()

        in_battle = game_in_battle_mode()
        if not in_battle:
            walk_until_start_battle()

        BATTLE_COUNT += 1
        sys.stdout.write("\nUma batalha foi iniciada ⚔️\n")
        sys.stdout.flush()

        time.sleep(4)

        if enemy_pokemon_is_catchable():
            catch_wild_pokemon()

        elif enemy_pokemon_is_rare():
            catch_wild_pokemon()

        else:
            run_away_wild_battle()
