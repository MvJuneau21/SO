import pygame
import threading
import time
import random

# --- Configurações do Jogo ---
LARGURA, ALTURA = 800, 600
FPS = 60
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)

LARGURA_RAQUETE, ALTURA_RAQUETE = 20, 100
RAIO_BOLA = 10

# --- Velocidades ---
VELOCIDADE_RAQUETE = 5
VELOCIDADE_INICIAL_BOLA = 5

# --- Variáveis Compartilhadas ---
placar_esquerda = 0
placar_direita = 0
executando = True
trava_placar = threading.Lock()

# --- Estruturas com múltiplas raquetes ---
NUM_RAQUETES = 3  # quantidade de raquetes por lado
raquetes_esquerda = [
    {"y": (i + 1) * ALTURA // (NUM_RAQUETES + 1) - ALTURA_RAQUETE // 2,
     "lock": threading.Lock(),
     "lado": "esquerda",
     "id": i}
    for i in range(NUM_RAQUETES)
]

raquetes_direita = [
    {"y": (i + 1) * ALTURA // (NUM_RAQUETES + 1) - ALTURA_RAQUETE // 2,
     "lock": threading.Lock(),
     "lado": "direita",
     "id": i}
    for i in range(NUM_RAQUETES)
]

# --- Lista de bolas ---
bolas = [
    {"x": LARGURA // 2, "y": ALTURA // 2,
     "vx": VELOCIDADE_INICIAL_BOLA, "vy": VELOCIDADE_INICIAL_BOLA,
     "lock": threading.Lock()},
    {"x": LARGURA // 3, "y": ALTURA // 3,
     "vx": -VELOCIDADE_INICIAL_BOLA, "vy": VELOCIDADE_INICIAL_BOLA,
     "lock": threading.Lock()}
]


def estrategia_raquete(raquete, bolas):
    """
    Define a estratégia de movimento da raquete.
    Cada raquete tem um comportamento diferente baseado no ID.
    """
    if raquete["id"] == 0:
        # Segue a bola mais próxima horizontalmente
        bola_alvo = min(bolas, key=lambda b: abs(b["x"] - (0 if raquete["lado"] == "esquerda" else LARGURA)))
        return bola_alvo["y"]

    elif raquete["id"] == 1:
        # Segue a média das bolas
        return sum([b["y"] for b in bolas]) / len(bolas)

    else:
        # Segue uma bola escolhida ao acaso, com erro aleatório
        bola_alvo = random.choice(bolas)
        return bola_alvo["y"] + random.randint(-50, 50)


def thread_raquete(raquete):
    global executando
    lado = raquete["lado"]
    idx = raquete["id"]
    print(f"--- [INFO] Raquete {idx+1} ({lado}) iniciada ---")

    while executando:
        alvo_y = estrategia_raquete(raquete, bolas)

        with raquete["lock"]:
            if raquete["y"] + ALTURA_RAQUETE / 2 < alvo_y:
                raquete["y"] += VELOCIDADE_RAQUETE
            elif raquete["y"] + ALTURA_RAQUETE / 2 > alvo_y:
                raquete["y"] -= VELOCIDADE_RAQUETE
            raquete["y"] = max(0, min(raquete["y"], ALTURA - ALTURA_RAQUETE))

        time.sleep(1 / FPS)


def thread_bola(idx):
    global placar_esquerda, placar_direita, executando
    bola = bolas[idx]
    print(f"--- [INFO] Bola {idx+1} iniciada ---")

    while executando:
        with bola["lock"]:
            bola["x"] += bola["vx"]
            bola["y"] += bola["vy"]

            # Colisão com as paredes
            if bola["y"] - RAIO_BOLA < 0 or bola["y"] + RAIO_BOLA > ALTURA:
                bola["vy"] *= -1

            # Colisão com raquetes da esquerda
            if bola["x"] - RAIO_BOLA < LARGURA_RAQUETE:
                bateu = False
                for r in raquetes_esquerda:
                    with r["lock"]:
                        if r["y"] < bola["y"] < r["y"] + ALTURA_RAQUETE:
                            bola["vx"] *= -1
                            bola["vy"] = random.choice([-1, 1]) * abs(bola["vy"])
                            bateu = True
                            break
                if not bateu:
                    with trava_placar:
                        placar_direita += 1
                    bola["x"], bola["y"] = LARGURA // 2, ALTURA // 2
                    bola["vx"] = VELOCIDADE_INICIAL_BOLA
                    bola["vy"] = random.choice([-1, 1]) * VELOCIDADE_INICIAL_BOLA

            # Colisão com raquetes da direita
            if bola["x"] + RAIO_BOLA > LARGURA - LARGURA_RAQUETE:
                bateu = False
                for r in raquetes_direita:
                    with r["lock"]:
                        if r["y"] < bola["y"] < r["y"] + ALTURA_RAQUETE:
                            bola["vx"] *= -1
                            bola["vy"] = random.choice([-1, 1]) * abs(bola["vy"])
                            bateu = True
                            break
                if not bateu:
                    with trava_placar:
                        placar_esquerda += 1
                    bola["x"], bola["y"] = LARGURA // 2, ALTURA // 2
                    bola["vx"] = -VELOCIDADE_INICIAL_BOLA
                    bola["vy"] = random.choice([-1, 1]) * VELOCIDADE_INICIAL_BOLA

        time.sleep(1 / FPS)


# --- Inicialização do Pygame ---
pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Pong Multithreaded - Raquetes Independentes")
relogio = pygame.time.Clock()
fonte_placar = pygame.font.Font(None, 74)

# --- Criação e Início das Threads ---
for r in (raquetes_esquerda + raquetes_direita)*2:
    threading.Thread(target=thread_raquete, args=(r,), daemon=True).start()

for i in range(len(bolas)):
    threading.Thread(target=thread_bola, args=(i,), daemon=True).start()

# --- Loop Principal do Jogo ---
ultimo_log = time.time()

while executando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

    tela.fill(PRETO)

    # Raquetes esquerda
    for r in raquetes_esquerda:
        with r["lock"]:
            pygame.draw.rect(tela, VERMELHO, (0, r["y"], LARGURA_RAQUETE, ALTURA_RAQUETE))

    # Raquetes direita
    for r in raquetes_direita:
        with r["lock"]:
            pygame.draw.rect(tela, AZUL, (LARGURA - LARGURA_RAQUETE, r["y"], LARGURA_RAQUETE, ALTURA_RAQUETE))

    # Bolas
    for bola in bolas:
        with bola["lock"]:
            pygame.draw.circle(tela, BRANCO, (int(bola["x"]), int(bola["y"])), RAIO_BOLA)

    # Placar
    with trava_placar:
        texto_placar = fonte_placar.render(f"{placar_esquerda}  {placar_direita}", True, BRANCO)
    tela.blit(texto_placar, (LARGURA // 2 - texto_placar.get_width() // 2, 10))

    pygame.display.flip()
    relogio.tick(FPS)

    # --- Impressão no Terminal a cada 0.5s ---
    if time.time() - ultimo_log > 0.5:
        for i, bola in enumerate(bolas, start=1):
            with bola["lock"]:
                print(f"[BOLA {i}] Posição (X, Y): ({bola['x']:.2f}, {bola['y']:.2f})")

        pos_esq = ", ".join([f"Y={r['y']:.1f}" for r in raquetes_esquerda])
        pos_dir = ", ".join([f"Y={r['y']:.1f}" for r in raquetes_direita])
        print(f"[RAQUETES ESQUERDA] {pos_esq}")
        print(f"[RAQUETES DIREITA] {pos_dir}\n")

        ultimo_log = time.time()



# --- Finalização ---
pygame.quit()
print("--- [INFO] Programa encerrado ---")
