import math
import random
import sys

import pygame


LARGURA, ALTURA = 1180, 700
FPS = 60

FUNDO = (22, 24, 34)
PAINEL = (34, 38, 54)
BORDA = (62, 68, 94)
TEXTO = (235, 238, 245)
SUAVE = (150, 158, 182)
DESTAQUE = (255, 205, 60)
OK = (90, 225, 130)
RUIM = (245, 95, 95)
COR_J1 = (95, 165, 255)
COR_J2 = (255, 150, 90)

BRANCO = (240, 240, 240)
AMARELO = (255, 213, 0)
VERMELHO = (200, 30, 30)
LARANJA = (255, 120, 0)
VERDE = (0, 155, 72)
AZUL = (0, 70, 173)
CORPO = (16, 16, 18)

NIVEIS = [("Iniciante", 180), ("Fácil", 120), ("Médio", 80),
          ("Difícil", 55), ("Mestre", 35), ("Lenda", 20)]
TAM_EMBARALHAMENTO = 25
INSPECAO = 10.0
TRAVA_DICA = 0.0

NORMAIS = {"U": (0, 1, 0), "D": (0, -1, 0), "R": (1, 0, 0),
           "L": (-1, 0, 0), "F": (0, 0, 1), "B": (0, 0, -1)}
LETRA_DA_NORMAL = {v: k for k, v in NORMAIS.items()}
COR_LETRA = {"U": BRANCO, "D": AMARELO, "R": VERMELHO, "L": LARANJA, "F": VERDE, "B": AZUL}
EIXO = {"U": 1, "D": 1, "R": 0, "L": 0, "F": 2, "B": 2}
GIROS = {"U": (1, 1, -1), "D": (1, -1, 1), "R": (0, 1, -1),
         "L": (0, -1, 1), "F": (2, 1, -1), "B": (2, -1, 1),
         "M": (0, 0, 1), "E": (1, 0, 1), "S": (2, 0, -1)}
SEGUE = {"M": "L", "E": "D", "S": "F"}
ROTACOES = {"x": (0, -1), "y": (1, -1), "z": (2, -1)}
VIRAR = "x2"


def girar_vetor(v, eixo, q):
    """Gira um vetor q quartos de volta (90 graus) em torno de um eixo."""
    x, y, z = v
    if eixo == 0:
        return (x, -z * q, y * q)
    if eixo == 1:
        return (z * q, y, -x * q)
    return (-y * q, x * q, z)


class Peca:
    def __init__(self, pos, adesivos):
        self.pos = pos
        self.ad = adesivos


class Cubo:
    def __init__(self):
        self.pecas = []
        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                for z in (-1, 0, 1):
                    if (x, y, z) == (0, 0, 0):
                        continue
                    ad = {}
                    for letra, n in NORMAIS.items():
                        if x == n[0] != 0 or y == n[1] != 0 or z == n[2] != 0:
                            ad[n] = letra
                    self.pecas.append(Peca((x, y, z), ad))

    def aplicar(self, mov):
        """Aplica 'R', "R'", 'R2', 'M' ou (cubo inteiro) 'x2' instantaneamente."""
        face = mov[0]
        vezes = 2 if mov.endswith("2") else 1
        if face in ROTACOES:                          # giro do cubo inteiro
            eixo, q = ROTACOES[face]
            camada = None
        else:
            eixo, camada, q = GIROS[face]
        if mov.endswith("'"):
            q = -q
        for _ in range(vezes):
            for p in self.pecas:
                if camada is None or p.pos[eixo] == camada:
                    p.pos = girar_vetor(p.pos, eixo, q)
                    p.ad = {girar_vetor(n, eixo, q): c for n, c in p.ad.items()}

    def progresso(self):
        """Quantos dos 54 adesivos combinam com o centro da sua face (o centro define a cor)."""
        centro = {}
        for p in self.pecas:
            if sum(abs(v) for v in p.pos) == 1:
                for n, c in p.ad.items():
                    centro[n] = c
        return sum(1 for p in self.pecas for n, c in p.ad.items() if centro[n] == c)

    def resolvido(self):
        return self.progresso() == 54


def gerar_embaralhamento(n):
    movs = []
    while len(movs) < n:
        f = random.choice("URFDLB")
        if movs and movs[-1][0] == f:
            continue
        if len(movs) >= 2 and EIXO[f] == EIXO[movs[-1][0]] == EIXO[movs[-2][0]]:
            continue
        movs.append(f + random.choice(["", "'"]))
    return movs


def inverso(movs):
    return [m[0] if m.endswith("'") else m[0] + "'" for m in reversed(movs)]


def simplificar(movs):
    """Junta giros seguidos da mesma face: R R' some, R R vira R2, etc.
    Devolve lista de (face, quartos) com quartos em 1, 2 ou 3."""
    pilha = []
    for m in movs:
        f = m[0]
        q = 3 if m.endswith("'") else 1
        if pilha and pilha[-1][0] == f:
            novo = (pilha[-1][1] + q) % 4
            pilha.pop()
            if novo:
                pilha.append((f, novo))
        else:
            pilha.append((f, q))
    return pilha


def nome_giro(f, q):
    return f if q == 1 else (f + "2" if q == 2 else f + "'")


def compactar(movs):
    """Para mostrar na tela: 'R R' vira 'R2'."""
    saida, i = [], 0
    while i < len(movs):
        if i + 1 < len(movs) and movs[i] == movs[i + 1] and movs[i][0].isupper():
            saida.append(movs[i][0] + "2")
            i += 2
        else:
            saida.append(movs[i])
            i += 1
    return saida


def girar_orientacao(mapa, mov):
    """Atualiza o mapa 'letra de agora -> letra do cubo original' depois de virar o cubo inteiro."""
    eixo, q = ROTACOES[mov[0]]
    if mov.endswith("'"):
        q = -q
    for _ in range(2 if mov.endswith("2") else 1):
        mapa = {l: mapa[LETRA_DA_NORMAL[girar_vetor(NORMAIS[l], eixo, -q)]] for l in "URFDLB"}
    return mapa


def traduzir(m, mapa):
    """Traduz um giro (face ou fatia) entre dois quadros de referência."""
    f, anti = m[0], m.endswith("'")
    if f in "URFDLB":
        return mapa[f] + ("'" if anti else "")
    seg = mapa[SEGUE[f]]
    nova = {"L": "M", "R": "M", "D": "E", "U": "E", "F": "S", "B": "S"}[seg]
    if seg != SEGUE[nova]:
        anti = not anti
    return nova + ("'" if anti else "")


def para_quadro_original(movs):
    """Converte o que o jogador apertou (com o cubo virado) para o quadro do cubo original."""
    mapa = {l: l for l in "URFDLB"}
    saida = []
    for m in movs:
        if m[0] in ROTACOES:
            mapa = girar_orientacao(mapa, m)
        else:
            saida.append(traduzir(m, mapa))
    return saida, mapa


def proxima_dica(embaralhamento, movs_jogador):
    orig, mapa = para_quadro_original(movs_jogador)
    pilha = simplificar(embaralhamento + orig)
    if not pilha:
        return None
    f, q = pilha[-1]
    volta = {v: k for k, v in mapa.items()}
    if q == 2:
        return traduzir(f, volta)[0] + "2"
    return traduzir(nome_giro(f, (4 - q) % 4), volta)


DIST = 14.0
H = 0.97
S = 0.80


def _moldes():
    moldes = {}
    for n in NORMAIS.values():
        eixo = [i for i in range(3) if n[i] != 0][0]
        outros = [i for i in range(3) if i != eixo]
        quad, adesivo = [], []
        for sb, sc in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            for escala, lista, folga in ((H, quad, 0.0), (H * S, adesivo, 0.004)):
                v = [0.0, 0.0, 0.0]
                v[eixo] = n[eixo] * (H + folga)
                v[outros[0]] = sb * escala
                v[outros[1]] = sc * escala
                lista.append(tuple(v))
        moldes[n] = (quad, adesivo)
    return moldes


MOLDES = _moldes()


def desenhar_cubo(tela, cubo, cx, cy, zoom, ax, ay, anim=None):
    """anim = (eixo, camada, angulo) enquanto uma camada está girando."""
    cax, sax = math.cos(ax), math.sin(ax)
    cay, say = math.cos(ay), math.sin(ay)

    def cam(v):
        x, y, z = v
        x, z = x * cay + z * say, -x * say + z * cay
        y, z = y * cax - z * sax, y * sax + z * cax
        return x, y, z

    a_eixo = a_camada = 0
    ca = sa = 0.0
    if anim:
        a_eixo, a_camada, a_ang = anim
        ca, sa = math.cos(a_ang), math.sin(a_ang)

    def girar(v):
        x, y, z = v
        if a_eixo == 0:
            return x, y * ca - z * sa, y * sa + z * ca
        if a_eixo == 1:
            return x * ca + z * sa, y, -x * sa + z * ca
        return x * ca - y * sa, x * sa + y * ca, z

    faces = []
    for p in cubo.pecas:
        movendo = anim is not None and (a_camada is None or p.pos[a_eixo] == a_camada)
        c = (p.pos[0] * 2.0, p.pos[1] * 2.0, p.pos[2] * 2.0)
        for n, (quad, adesivo) in MOLDES.items():
            cor = p.ad.get(n)
            if cor is None and (anim is None or a_camada is None):
                continue                      # face interna: nunca aparece
            fc = (c[0] + n[0] * H, c[1] + n[1] * H, c[2] + n[2] * H)
            nv = n
            if movendo:
                fc, nv = girar(fc), girar(n)
            fc, nv = cam(fc), cam(nv)
            if nv[0] * -fc[0] + nv[1] * -fc[1] + nv[2] * (DIST - fc[2]) <= 0:
                continue                      # de costas para a câmera
            faces.append((fc[2], c, quad, adesivo, cor, movendo))
    faces.sort(key=lambda f: f[0])

    def proj(c, off, movendo):
        v = (c[0] + off[0], c[1] + off[1], c[2] + off[2])
        if movendo:
            v = girar(v)
        x, y, z = cam(v)
        f = zoom / (DIST - z)
        return (cx + x * f, cy - y * f)

    for _, c, quad, adesivo, cor, movendo in faces:
        pygame.draw.polygon(tela, CORPO, [proj(c, o, movendo) for o in quad])
        if cor is not None:
            pygame.draw.polygon(tela, COR_LETRA[cor], [proj(c, o, movendo) for o in adesivo])


def ponto_no_poligono(p, pts):
    """True se o ponto p = (x, y) está dentro do polígono."""
    x, y = p
    dentro = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def face_no_ponto(cubo, cx, cy, zoom, ax, ay, ponto):
    """Devolve a letra da face (U D R L F B) que está sob o ponto da tela, ou None."""
    cax, sax = math.cos(ax), math.sin(ax)
    cay, say = math.cos(ay), math.sin(ay)

    def cam(v):
        x, y, z = v
        x, z = x * cay + z * say, -x * say + z * cay
        y, z = y * cax - z * sax, y * sax + z * cax
        return x, y, z

    melhor = None
    for p in cubo.pecas:
        c = (p.pos[0] * 2.0, p.pos[1] * 2.0, p.pos[2] * 2.0)
        for n, (quad, adesivo) in MOLDES.items():
            if n not in p.ad:
                continue
            fc = cam((c[0] + n[0] * H, c[1] + n[1] * H, c[2] + n[2] * H))
            nv = cam(n)
            if nv[0] * -fc[0] + nv[1] * -fc[1] + nv[2] * (DIST - fc[2]) <= 0:
                continue
            pts = []
            for o in quad:
                x, y, z = cam((c[0] + o[0], c[1] + o[1], c[2] + o[2]))
                f = zoom / (DIST - z)
                pts.append((cx + x * f, cy - y * f))
            if ponto_no_poligono(ponto, pts):
                if melhor is None or fc[2] > melhor[0]:
                    melhor = (fc[2], LETRA_DA_NORMAL[n])
    return melhor[1] if melhor else None


class Jogador:
    def __init__(self, nome, humano, cor):
        self.nome = nome
        self.humano = humano
        self.cor = cor
        self.painel = (0, 0, 0, 0)
        self.centro = (0, 0)
        self.zoom = 700
        self.reiniciar()

    def reiniciar(self):
        self.cubo = Cubo()
        self.fila = []
        self.anim = None
        self.movs = []
        self.tempos = []
        self.prog = []
        self.ax, self.ay = 0.5, -0.7
        self.fim = None
        self.dica = ""
        self.dica_t = 0.0
        self.trava = 0.0
        self.parado = 0.0
        self.agenda = []

    def enfileirar(self, mov, registrar=True, t=0.0, dur=None):
        self.fila.append((mov, registrar, dur))
        if registrar:
            self.movs.append(mov)
            self.tempos.append(t)
            self.parado = 0.0

    def ocupado(self):
        return bool(self.fila) or self.anim is not None

    def atualizar(self, dt, t):
        if self.anim is None and self.fila:
            mov, reg, dur = self.fila.pop(0)
            if dur is None:
                dur = max(0.05, 0.18 - 0.035 * len(self.fila))
            self.anim = {"mov": mov, "t": 0.0, "dur": dur, "reg": reg}
        if self.anim:
            self.anim["t"] += dt
            if self.anim["t"] >= self.anim["dur"]:
                self.cubo.aplicar(self.anim["mov"])
                reg = self.anim["reg"]
                self.anim = None
                if reg:
                    self.prog.append((t, self.cubo.progresso()))
        self.dica_t = max(0.0, self.dica_t - dt)
        self.trava = max(0.0, self.trava - dt)

    def angulo_anim(self):
        if not self.anim:
            return None
        mov = self.anim["mov"]
        frac = min(1.0, self.anim["t"] / self.anim["dur"])
        frac = frac * frac * (3 - 2 * frac)
        if mov[0] in ROTACOES:
            eixo, q = ROTACOES[mov[0]]
            camada = None
            quartos = 2 if mov.endswith("2") else 1
        else:
            eixo, camada, q = GIROS[mov[0]]
            quartos = 1
        if mov.endswith("'"):
            q = -q
        return (eixo, camada, q * quartos * (math.pi / 2) * frac)


def formatar(t):
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def analisar(j, t_fim):
    eventos = [(t, m) for t, m in zip(j.tempos, j.movs) if m[0].isupper()]
    movs = [m for _, m in eventos]
    tempos = [t for t, _ in eventos]
    n = len(movs)
    pilha = simplificar(para_quadro_original(j.movs)[0])
    efetivos = sum(min(q, 4 - q) for _, q in pilha)
    desperdicio = n - efetivos
    triplas = sum(1 for i in range(2, n) if movs[i] == movs[i - 1] == movs[i - 2])
    pausas = []
    for i in range(n):
        anterior = tempos[i - 1] if i > 0 else 0.0
        pausas.append((tempos[i] - anterior, i))
    maior_pausa = max(pausas) if pausas else (0.0, 0)
    primeiro = tempos[0] if n else t_fim
    tps = n / t_fim if t_fim > 0 else 0.0

    melhor, ultimo_t, estagnacao = -1, 0.0, (0.0, 0)
    for t, p in j.prog:
        if p > melhor:
            if t - ultimo_t > estagnacao[0] and melhor >= 0:
                estagnacao = (t - ultimo_t, melhor)
            melhor, ultimo_t = p, t

    dados = {"tempo": t_fim, "n": n, "efetivos": efetivos, "desperdicio": desperdicio,
             "tps": tps, "maior_pausa": maior_pausa, "primeiro": primeiro,
             "estagnacao": estagnacao, "triplas": triplas}

    dicas = []
    if n == 0:
        dicas.append("Você não fez nenhum movimento. Use a inspeção para planejar e comece logo!")
        dados["dicas"] = dicas
        return dados
    if primeiro > 12 and n > 5:
        dicas.append(f"Você demorou {primeiro:.0f}s para o 1º movimento. Planeje a primeira "
                     f"etapa durante a inspeção e comece a girar assim que o relógio disparar.")
    if maior_pausa[0] > 4:
        f = movs[maior_pausa[1]]
        dicas.append(f"Maior pausa: {maior_pausa[0]:.1f}s antes do movimento nº {maior_pausa[1] + 1} ({f}). "
                     f"Treine olhar a próxima peça ENQUANTO gira a atual.")
    if desperdicio >= 2:
        dicas.append(f"{desperdicio} movimentos se cancelaram (ex.: R seguido de R'). "
                     f"Confirme o plano na cabeça antes de girar.")
    if triplas:
        dicas.append(f"Você girou a mesma face 3 vezes seguidas {triplas}x. "
                     f"Um giro no sentido contrário (Shift) faz o mesmo em 1 movimento.")
    if estagnacao[0] > max(8.0, t_fim * 0.25):
        pct = int(estagnacao[1] / 54 * 100)
        dicas.append(f"Você ficou {estagnacao[0]:.0f}s sem avançar com {pct}% do cubo montado. "
                     f"Treine esse trecho (ex.: o 'sexy move' R U R' U') até virar automático.")
    if tps < 1.5:
        dicas.append(f"Velocidade: {tps:.1f} mov/s. Decore sequências curtas e gire sem pensar peça a peça.")
    elif tps < 3.5:
        dicas.append(f"Velocidade: {tps:.1f} mov/s, boa! Para subir de nível, reduza as pausas entre os movimentos.")
    else:
        dicas.append(f"Velocidade: {tps:.1f} mov/s, nível avançado! O foco agora é gastar menos movimentos.")
    if len(dicas) == 1:
        dicas.insert(0, "Sem erros evidentes. Continue treinando a fluidez e a leitura antecipada das peças.")
    dados["dicas"] = dicas[:4]
    return dados


def texto(tela, fonte, txt, cor, x, y, alin="esq"):
    img = fonte.render(txt, True, cor)
    w = img.get_width()
    if alin == "centro":
        x -= w // 2
    elif alin == "dir":
        x -= w
    tela.blit(img, (x, y))
    return w


def quebrar(fonte, tokens, largura):
    linhas, atual = [], ""
    for t in tokens:
        teste = (atual + " " + t).strip()
        if atual and fonte.size(teste)[0] > largura:
            linhas.append(atual)
            atual = t
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def quebrar_texto(fonte, frase, largura):
    return quebrar(fonte, frase.split(" "), largura)


MODOS = [("solo", "Treino solo", "Resolva sozinho com timer, dicas e análise no final"),
         ("pc", "Contra o computador", "Corrida contra o computador, em 6 níveis")]


class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Cubo Mágico 3D")
        self.relogio = pygame.time.Clock()
        ui = "segoeui,arial"
        mono = "consolas,couriernew,arial"
        self.f_p = pygame.font.SysFont(ui, 16)
        self.f_m = pygame.font.SysFont(ui, 20, bold=True)
        self.f_g = pygame.font.SysFont(ui, 30, bold=True)
        self.f_t = pygame.font.SysFont(mono, 38, bold=True)
        self.f_titulo = pygame.font.SysFont(ui, 52, bold=True)
        self.f_mov = pygame.font.SysFont(mono, 17, bold=True)
        self.f_grande = pygame.font.SysFont(mono, 64, bold=True)
        self.estado = "menu"
        self.sel = 0
        self.nivel = 1
        self.modo = "solo"
        self.jogadores = []
        self.embaralhamento = []
        self.t = 0.0
        self.inspecao = 0.0
        self.pausado = False
        self.vencedor = None
        self.setas_giram_faces = False
        self.arrastando = None
        self.moveu = 0
        self.giro_menu = 0.0
        self.flash = 0.0
        self.analises = []
        self.resultado_titulo = ""

    def iniciar_rodada(self):
        self.embaralhamento = gerar_embaralhamento(TAM_EMBARALHAMENTO)
        if self.modo == "solo":
            self.jogadores = [Jogador("Você", True, COR_J1)]
            self.jogadores[0].painel = (10, 66, 780, 600)
            self.jogadores[0].centro = (400, 66 + 246)
            self.jogadores[0].zoom = 540
        else:
            nome2 = "Computador - " + NIVEIS[self.nivel][0]
            self.jogadores = [Jogador("Você", True, COR_J1),
                              Jogador(nome2, False, COR_J2)]
            for i, j in enumerate(self.jogadores):
                px = 10 + i * 585
                j.painel = (px, 66, 575, 600)
                j.centro = (px + 287, 66 + 250)
                j.zoom = 520
        for j in self.jogadores:
            j.reiniciar()
            for m in self.embaralhamento:
                j.enfileirar(m, registrar=False, dur=0.07)
        self.estado = "embaralhando"
        self.t = 0.0
        self.pausado = False
        self.vencedor = None
        self.inspecao = INSPECAO
        self.flash = 0.0

    def comecar(self):
        self.estado = "corrida"
        self.t = 0.0
        self.flash = 1.0
        for j in self.jogadores:
            j.prog = [(0.0, j.cubo.progresso())]
        if self.modo == "pc":
            self.agendar_pc(self.jogadores[1], NIVEIS[self.nivel][1])

    def agendar_pc(self, j, alvo):
        plano = inverso(self.embaralhamento)
        pesos = [random.uniform(0.5, 1.5) for _ in plano]
        total = sum(pesos)
        t = 0.0
        j.agenda = []
        for m, w in zip(plano, pesos):
            atraso = alvo * w / total
            t += atraso
            j.agenda.append((t, m, max(0.05, min(0.2, atraso * 0.7))))

    def atualizar(self, dt):
        self.giro_menu += dt * 0.6
        self.flash = max(0.0, self.flash - dt)
        if self.estado == "embaralhando":
            for j in self.jogadores:
                j.atualizar(dt, 0.0)
            if not any(j.ocupado() for j in self.jogadores):
                self.estado = "pronto"
        elif self.estado == "pronto":
            for j in self.jogadores:
                j.atualizar(dt, 0.0)
            self.inspecao -= dt
            if self.inspecao <= 0:
                self.comecar()
        elif self.estado == "corrida" and not self.pausado:
            self.t += dt
            self.atualizar_corrida(dt)

    def atualizar_corrida(self, dt):
        for j in self.jogadores:
            if j.fim is not None:
                continue
            if not j.humano:
                while j.agenda and j.agenda[0][0] <= self.t:
                    _, m, dur = j.agenda.pop(0)
                    j.enfileirar(m, True, self.t, dur)
            else:
                j.parado += dt
            j.atualizar(dt, self.t)
            pronto = j.cubo.resolvido() and not j.ocupado() and (j.movs or not j.humano)
            if not j.humano:
                pronto = pronto and not j.agenda
            if pronto:
                j.fim = self.t
        terminaram = [j for j in self.jogadores if j.fim is not None]
        if terminaram:
            self.vencedor = min(terminaram, key=lambda j: j.fim)
            self.encerrar()

    def encerrar(self):
        self.estado = "resultado"
        self.analises = []
        for j in self.jogadores:
            t_fim = j.fim if j.fim is not None else self.t
            if j.fim is None:
                j.prog.append((self.t, j.cubo.progresso()))
            self.analises.append(analisar(j, t_fim))
        if self.modo == "solo":
            self.resultado_titulo = "CUBO RESOLVIDO!"
        elif self.vencedor is self.jogadores[0]:
            self.resultado_titulo = "VOCÊ VENCEU!"
        else:
            self.resultado_titulo = "O COMPUTADOR VENCEU"

    def sair(self):
        pygame.quit()
        sys.exit()

    def mover(self, j, letra, anti):
        if self.estado != "corrida" or self.pausado or j.fim is not None or not j.humano:
            return
        if j.trava > 0 or len(j.fila) >= 8:
            return
        j.enfileirar(letra + ("'" if anti else ""), True, self.t)

    def virar(self, j):
        """ESPAÇO: vira o cubo de cabeça para baixo (branco <-> amarelo)."""
        if self.estado not in ("pronto", "corrida") or self.pausado or j.fim is not None or not j.humano:
            return
        if len(j.fila) >= 8:
            return
        j.enfileirar(VIRAR, True, self.t if self.estado == "corrida" else 0.0, 0.5)

    def pedir_dica(self):
        j = self.jogadores[0]
        if self.estado != "corrida" or self.pausado or j.fim is not None:
            return
        d = proxima_dica(self.embaralhamento, j.movs)
        if d:
            j.dica = f"Dica: gire {d}  (cubo travado {TRAVA_DICA:.0f}s)"
            j.dica_t = 6.0
            j.trava = TRAVA_DICA

    def tratar_evento(self, e):
        if e.type == pygame.QUIT:
            self.sair()
        if self.estado == "menu":
            self.evento_menu(e)
        elif self.estado == "nivel":
            self.evento_nivel(e)
        elif self.estado == "resultado":
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN or e.key == pygame.K_ESCAPE:
                    self.estado = "menu"
                elif e.key == pygame.K_SPACE or e.key == pygame.K_F5:
                    self.iniciar_rodada()
        else:
            self.evento_jogo(e)

    def evento_menu(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_UP:
                self.sel = (self.sel - 1) % len(MODOS)
            elif e.key == pygame.K_DOWN:
                self.sel = (self.sel + 1) % len(MODOS)
            elif e.key in (pygame.K_1, pygame.K_2):
                self.sel = {pygame.K_1: 0, pygame.K_2: 1}[e.key]
                self.escolher_modo()
            elif e.key == pygame.K_RETURN:
                self.escolher_modo()
            elif e.key == pygame.K_ESCAPE:
                self.sair()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(len(MODOS)):
                x, y, w, h = self.retangulo_menu(i)
                if x <= e.pos[0] <= x + w and y <= e.pos[1] <= y + h:
                    self.sel = i
                    self.escolher_modo()

    def retangulo_menu(self, i):
        return (330, 250 + i * 115, 520, 90)

    def escolher_modo(self):
        self.modo = MODOS[self.sel][0]
        if self.modo == "pc":
            self.estado = "nivel"
        else:
            self.iniciar_rodada()

    def evento_nivel(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_UP:
                self.nivel = (self.nivel - 1) % len(NIVEIS)
            elif e.key == pygame.K_DOWN:
                self.nivel = (self.nivel + 1) % len(NIVEIS)
            elif pygame.K_1 <= e.key <= pygame.K_6:
                self.nivel = e.key - pygame.K_1
                self.iniciar_rodada()
            elif e.key == pygame.K_RETURN:
                self.iniciar_rodada()
            elif e.key == pygame.K_ESCAPE:
                self.estado = "menu"
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(len(NIVEIS)):
                if 330 <= e.pos[0] <= 850 and 200 + i * 62 <= e.pos[1] <= 200 + i * 62 + 54:
                    self.nivel = i
                    self.iniciar_rodada()

    def evento_jogo(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.arrastando = self.jogador_sob_mouse(e.pos)
            self.moveu = 0
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            self.girar_com_mouse(e.pos, True)                  # botão direito = anti-horário
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.arrastando is not None and self.moveu < 6:   # foi um clique, não um arrasto
                self.girar_com_mouse(e.pos, False)               # botão esquerdo = horário
            self.arrastando = None
        elif e.type == pygame.MOUSEMOTION and self.arrastando is not None:
            self.moveu += abs(e.rel[0]) + abs(e.rel[1])
            if self.moveu >= 6:                                  # só gira a câmera se arrastou de verdade
                j = self.arrastando
                j.ay += e.rel[0] * 0.01
                j.ax = max(-1.4, min(1.4, j.ax + e.rel[1] * 0.01))
        elif e.type == pygame.KEYDOWN:
            self.tecla_jogo(e.key)

    def girar_com_mouse(self, pos, anti):
        """Clique em cima de uma face do cubo para girá-la."""
        j = self.jogadores[0]
        x, y, w, h = j.painel
        if not (x <= pos[0] <= x + w and y <= pos[1] <= y + h):
            return                          # clicou fora do seu cubo
        face = face_no_ponto(j.cubo, j.centro[0], j.centro[1], j.zoom, j.ax, j.ay, pos)
        if face:
            self.mover(j, face, anti)

    def jogador_sob_mouse(self, pos):
        for j in self.jogadores:
            x, y, w, h = j.painel
            if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                return j
        return self.jogadores[0] if self.modo == "solo" else None

    def tecla_jogo(self, k):
        mods = pygame.key.get_mods()
        if k == pygame.K_ESCAPE:
            self.estado = "menu"
            return
        if k == pygame.K_F5:
            self.iniciar_rodada()
            return
        if k == pygame.K_RETURN and self.estado == "pronto":
            self.comecar()
            return
        if k == pygame.K_SPACE:
            self.virar(self.jogadores[0])
            return
        if k == pygame.K_p and self.estado == "corrida":
            self.pausado = not self.pausado
            return
        if k == pygame.K_h:
            self.pedir_dica()
            return
        anti = bool(mods & pygame.KMOD_SHIFT)
        if k == pygame.K_TAB:
            self.setas_giram_faces = not self.setas_giram_faces
            return
        faces = {pygame.K_u: "U", pygame.K_d: "D", pygame.K_r: "R",
                 pygame.K_l: "L", pygame.K_f: "F", pygame.K_b: "B",
                 pygame.K_m: "M", pygame.K_e: "E", pygame.K_s: "S"}
        if self.setas_giram_faces:
            faces.update({pygame.K_UP: "U", pygame.K_DOWN: "D",
                          pygame.K_LEFT: "L", pygame.K_RIGHT: "R"})
        if k in faces:
            self.mover(self.jogadores[0], faces[k], anti)

    def camera_setas(self):
        if self.setas_giram_faces or not self.jogadores:
            return
        t = pygame.key.get_pressed()
        j = self.jogadores[0]
        if t[pygame.K_LEFT]:
            j.ay -= 0.03
        if t[pygame.K_RIGHT]:
            j.ay += 0.03
        if t[pygame.K_UP]:
            j.ax = max(-1.4, j.ax - 0.03)
        if t[pygame.K_DOWN]:
            j.ax = min(1.4, j.ax + 0.03)

    def desenhar(self):
        t = self.tela
        t.fill(FUNDO)
        if self.estado == "menu":
            self.desenhar_menu()
        elif self.estado == "nivel":
            self.desenhar_nivel()
        elif self.estado == "resultado":
            self.desenhar_resultado()
        else:
            self.desenhar_jogo()

    def cabecalho(self, titulo):
        pygame.draw.rect(self.tela, PAINEL, (0, 0, LARGURA, 56))
        texto(self.tela, self.f_g, "CUBO MÁGICO 3D", DESTAQUE, 20, 10)
        texto(self.tela, self.f_m, titulo, SUAVE, LARGURA - 20, 16, "dir")

    def desenhar_menu(self):
        self.cabecalho("Menu principal")
        texto(self.tela, self.f_titulo, "CUBO MÁGICO 3D", DESTAQUE, LARGURA // 2, 80, "centro")
        texto(self.tela, self.f_p, "Escolha um modo (↑ ↓ e Enter, números 1-2 ou clique)",
              SUAVE, LARGURA // 2, 160, "centro")
        for i, (_, nome, desc) in enumerate(MODOS):
            x, y, w, h = self.retangulo_menu(i)
            sel = i == self.sel
            pygame.draw.rect(self.tela, (52, 60, 92) if sel else PAINEL, (x, y, w, h), border_radius=14)
            pygame.draw.rect(self.tela, DESTAQUE if sel else BORDA, (x, y, w, h), 2, border_radius=14)
            texto(self.tela, self.f_g, f"{i + 1}  {nome}", TEXTO, x + 24, y + 12)
            texto(self.tela, self.f_p, desc, SUAVE, x + 24, y + 54)
        pequeno = Cubo()
        desenhar_cubo(self.tela, pequeno, 160, 420, 330, 0.5, self.giro_menu)
        desenhar_cubo(self.tela, pequeno, LARGURA - 160, 420, 330, 0.5, -self.giro_menu)
        texto(self.tela, self.f_p, "ESC = sair", SUAVE, 20, ALTURA - 30)

    def desenhar_nivel(self):
        self.cabecalho("Contra o computador")
        texto(self.tela, self.f_g, "Escolha o nível do computador", TEXTO, LARGURA // 2, 100, "centro")
        texto(self.tela, self.f_p, "↑ ↓ e Enter, números 1-6 ou clique  |  ESC volta",
              SUAVE, LARGURA // 2, 150, "centro")
        for i, (nome, seg) in enumerate(NIVEIS):
            x, y, w, h = 330, 200 + i * 62, 520, 54
            sel = i == self.nivel
            pygame.draw.rect(self.tela, (52, 60, 92) if sel else PAINEL, (x, y, w, h), border_radius=12)
            pygame.draw.rect(self.tela, DESTAQUE if sel else BORDA, (x, y, w, h), 2, border_radius=12)
            texto(self.tela, self.f_m, f"{i + 1}  {nome}", TEXTO, x + 20, y + 14)
            texto(self.tela, self.f_p, f"resolve em ~{formatar(seg)[:5]}", SUAVE, x + w - 20, y + 17, "dir")

    def desenhar_jogo(self):
        modo_txt = "Treino solo" if self.modo == "solo" else f"Contra o computador - nível {NIVEIS[self.nivel][0]}"
        self.cabecalho(modo_txt)
        for j in self.jogadores:
            self.desenhar_painel(j)
        if self.modo == "solo":
            self.desenhar_lateral_solo()
        if self.estado == "embaralhando":
            texto(self.tela, self.f_g, "Embaralhando...", DESTAQUE, LARGURA // 2, 74, "centro")
        elif self.estado == "pronto":
            self.desenhar_inspecao()
        elif self.estado == "corrida" and self.flash > 0:
            texto(self.tela, self.f_grande, "VAI!", OK, LARGURA // 2, 590, "centro")
        if self.pausado:
            texto(self.tela, self.f_grande, "PAUSADO", DESTAQUE, LARGURA // 2, 300, "centro")
        self.legenda()

    def legenda(self):
        txt = ("R L U D F B M E S = girar  |  Shift = anti-horário  |  Clique esq./dir. na face  |  "
               "ESPAÇO = virar cubo  |  Arrastar/setas = câmera  |  H = dica  |  P = pausa  |  ESC = menu")
        texto(self.tela, self.f_p, txt, SUAVE, 14, ALTURA - 26)

    def tempo_do(self, j):
        if j.fim is not None:
            return j.fim
        return self.t if self.estado == "corrida" else 0.0

    def desenhar_painel(self, j):
        t = self.tela
        px, py, pw, ph = j.painel
        pygame.draw.rect(t, PAINEL, (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(t, j.cor if j.fim is None else OK, (px, py, pw, ph), 2, border_radius=14)
        texto(t, self.f_m, j.nome, j.cor, px + 16, py + 12)
        texto(t, self.f_t, formatar(self.tempo_do(j)), TEXTO, px + pw - 16, py + 6, "dir")
        ultimo = compactar(j.movs)[-1] if j.movs else "-"
        texto(t, self.f_p, "Último movimento", SUAVE, px + 16, py + 50)
        texto(t, self.f_g, ultimo, DESTAQUE, px + 16, py + 68)
        desenhar_cubo(t, j.cubo, j.centro[0], j.centro[1], j.zoom, j.ax, j.ay, j.angulo_anim())
        # barra de progresso
        prog = j.cubo.progresso()
        by = py + 440
        pygame.draw.rect(t, (20, 22, 32), (px + 20, by, pw - 40, 14), border_radius=7)
        largura = int((pw - 40) * prog / 54)
        if largura > 0:
            pygame.draw.rect(t, OK if prog == 54 else j.cor, (px + 20, by, largura, 14), border_radius=7)
        texto(t, self.f_p, f"{int(prog / 54 * 100)}% montado", SUAVE, px + pw - 20, by + 18, "dir")
        # histórico
        texto(t, self.f_p, f"Movimentos ({len(j.movs)}):", SUAVE, px + 20, by + 18)
        tokens = compactar(j.movs)[-80:]
        linhas = quebrar(self.f_mov, tokens, pw - 40)[-4:]
        for i, ln in enumerate(linhas):
            texto(t, self.f_mov, ln, TEXTO, px + 20, by + 44 + i * 22)
        # mensagens
        msg, cor = "", SUAVE
        if j.dica_t > 0:
            msg, cor = j.dica, DESTAQUE
        elif j.humano and self.estado == "corrida" and j.fim is None and j.parado > 10:
            msg, cor = "Parado há mais de 10s: planeje o próximo passo!", RUIM
        elif not j.humano and self.estado == "corrida" and j.fim is None:
            msg = "O computador está resolvendo..."
        if msg:
            texto(t, self.f_p, msg, cor, px + pw // 2, py + ph - 26, "centro")

    def desenhar_lateral_solo(self):
        x, y, w, h = 800, 66, 370, 600
        pygame.draw.rect(self.tela, PAINEL, (x, y, w, h), border_radius=14)
        pygame.draw.rect(self.tela, BORDA, (x, y, w, h), 2, border_radius=14)
        texto(self.tela, self.f_m, "Controles", DESTAQUE, x + 18, y + 14)
        linhas = ["R L U D F B  →  gira a face (horário)",
                  "M E S  →  fatias do meio (M segue o L)",
                  "Shift + letra  →  anti-horário",
                  "Clique esq./dir. na face  →  horário/anti",
                  "ESPAÇO  →  vira o cubo (branco/amarelo)",
                  "Arrastar o mouse  →  gira a câmera",
                  "Setas  →  câmera  (TAB troca p/ faces)",
                  "H dica  |  P pausa  |  F5 refazer"]
        for i, ln in enumerate(linhas):
            texto(self.tela, self.f_p, ln, TEXTO, x + 18, y + 46 + i * 24)
        texto(self.tela, self.f_m, "Modo das setas", DESTAQUE, x + 18, y + 270)
        modo = "Faces (↑U ↓D ←L →R)" if self.setas_giram_faces else "Câmera"
        texto(self.tela, self.f_p, modo, OK, x + 18, y + 298)
        texto(self.tela, self.f_m, "Seu objetivo", DESTAQUE, x + 18, y + 340)
        for i, ln in enumerate(quebrar_texto(self.f_p, "Deixar as 6 faces de uma cor só no menor tempo. "
                                            "No fim você vê a análise de onde pode melhorar.", w - 36)):
            texto(self.tela, self.f_p, ln, SUAVE, x + 18, y + 372 + i * 22)

    def desenhar_inspecao(self):
        x, y, w, h = 10, 572, LARGURA - 20, 94
        pygame.draw.rect(self.tela, (46, 52, 80), (x, y, w, h), border_radius=12)
        pygame.draw.rect(self.tela, DESTAQUE, (x, y, w, h), 2, border_radius=12)
        texto(self.tela, self.f_g, f"INSPEÇÃO  {int(self.inspecao) + 1}s", DESTAQUE, x + 18, y + 8)
        texto(self.tela, self.f_p, "ENTER = começar agora   |   ESPAÇO = virar o cubo   |   gire a câmera e planeje",
              TEXTO, x + 300, y + 16)
        linhas = quebrar(self.f_mov, ["Embaralhamento:"] + self.embaralhamento, w - 36)
        for i, ln in enumerate(linhas[:2]):
            texto(self.tela, self.f_mov, ln, SUAVE, x + 18, y + 48 + i * 22)

    def desenhar_resultado(self):
        self.cabecalho("Resultado")
        t = self.tela
        perdeu = "COMPUTADOR VENCEU" in self.resultado_titulo
        texto(t, self.f_titulo, self.resultado_titulo, RUIM if perdeu else OK, LARGURA // 2, 62, "centro")
        n = len(self.jogadores)
        if n == 1:
            j, a = self.jogadores[0], self.analises[0]
            self.bloco_stats(j, a, 20, 130, 560, 250, True)
            self.bloco_texto("Onde melhorar", a["dicas"], 600, 130, 560, 250, 4)
            self.desenhar_grafico((20, 400, LARGURA - 40, 255))
        else:
            for i, (j, a) in enumerate(zip(self.jogadores, self.analises)):
                x = 20 + i * 585
                self.bloco_stats(j, a, x, 118, 565, 188, j is self.vencedor)
                if j.humano:
                    self.bloco_texto("Onde melhorar", a["dicas"], x, 314, 565, 192, 3)
                else:
                    nome, seg = NIVEIS[self.nivel]
                    expl = ["O computador conhece o embaralhamento e o desfaz ao contrário, "
                            "no ritmo do nível " + nome + ".",
                            f"Para vencê-lo neste nível, termine em menos de {formatar(seg)[:5]}."]
                    self.bloco_texto("Sobre o computador", expl, x, 314, 565, 192, 3)
            self.desenhar_grafico((20, 514, LARGURA - 40, 150))
        texto(t, self.f_p, "ESPAÇO = jogar de novo  |  ENTER = menu", SUAVE, LARGURA // 2, ALTURA - 26, "centro")

    def bloco_stats(self, j, a, x, y, w, h, venceu):
        t = self.tela
        pygame.draw.rect(t, PAINEL, (x, y, w, h), border_radius=12)
        pygame.draw.rect(t, OK if (venceu and j.fim is not None) else BORDA, (x, y, w, h), 2, border_radius=12)
        texto(t, self.f_m, j.nome, j.cor, x + 14, y + 8)
        if venceu and j.fim is not None and len(self.jogadores) > 1:
            texto(t, self.f_p, "VENCEDOR", OK, x + w - 14, y + 12, "dir")
        linhas = [("Tempo", formatar(a["tempo"]) if j.fim is not None else "não terminou"),
                  ("Movimentos", str(a["n"])),
                  ("Movimentos por segundo", f"{a['tps']:.2f}")]
        if j.humano:
            linhas += [("Movimentos úteis", f"{a['efetivos']}  (desperdício: {a['desperdicio']})"),
                       ("Maior pausa entre movimentos", f"{a['maior_pausa'][0]:.1f}s"),
                       ("Demora até o 1º movimento", f"{a['primeiro']:.1f}s")]
        passo = 28 if h > 220 else 23
        for i, (k, v) in enumerate(linhas):
            texto(t, self.f_p, k, SUAVE, x + 14, y + 40 + i * passo)
            texto(t, self.f_p, v, TEXTO, x + w - 14, y + 40 + i * passo, "dir")

    def bloco_texto(self, titulo, itens, x, y, w, h, maximo):
        t = self.tela
        pygame.draw.rect(t, PAINEL, (x, y, w, h), border_radius=12)
        pygame.draw.rect(t, BORDA, (x, y, w, h), 2, border_radius=12)
        texto(t, self.f_m, titulo, DESTAQUE, x + 14, y + 8)
        yy = y + 38
        for item in itens[:maximo]:
            linhas = quebrar_texto(self.f_p, item, w - 52)
            for k, ln in enumerate(linhas):
                if k == 0:
                    texto(t, self.f_p, "•", DESTAQUE, x + 16, yy)
                texto(t, self.f_p, ln, TEXTO, x + 34, yy)
                yy += 20
            yy += 6

    def desenhar_grafico(self, rect):
        t = self.tela
        gx, gy, gw, gh = rect
        pygame.draw.rect(t, PAINEL, (gx, gy, gw, gh), border_radius=12)
        pygame.draw.rect(t, BORDA, (gx, gy, gw, gh), 2, border_radius=12)
        texto(t, self.f_m, "Progresso do cubo ao longo do tempo", DESTAQUE, gx + 14, gy + 6)
        ex, ey, ew, eh = gx + 56, gy + 36, gw - 90, gh - 36 - 28
        pygame.draw.rect(t, (20, 22, 32), (ex, ey, ew, eh))
        tmax = max([p[-1][0] for p in (j.prog for j in self.jogadores) if p] + [1.0])
        for k in range(0, 5):
            yy = ey + eh - eh * k / 4
            pygame.draw.line(t, BORDA, (ex, yy), (ex + ew, yy), 1)
            if k % 2 == 0 or eh > 120:
                texto(t, self.f_p, f"{k * 25}%", SUAVE, ex - 8, yy - 10, "dir")
        texto(t, self.f_p, "0s", SUAVE, ex, ey + eh + 4)
        texto(t, self.f_p, f"{tmax:.0f}s", SUAVE, ex + ew, ey + eh + 4, "dir")
        for j in self.jogadores:
            pts, ultimo_y = [], None
            for tt, p in j.prog:
                xx = ex + ew * tt / tmax
                if ultimo_y is not None:
                    pts.append((xx, ultimo_y))
                yy = ey + eh - eh * p / 54
                pts.append((xx, yy))
                ultimo_y = yy
            if len(pts) >= 2:
                pygame.draw.lines(t, j.cor, False, pts, 3)
        lx = gx + gw - 14
        for j in reversed(self.jogadores):
            lx -= texto(t, self.f_p, j.nome, j.cor, lx, gy + 10, "dir") + 24

    def rodar(self):
        while True:
            dt = min(self.relogio.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                self.tratar_evento(e)
            if self.estado in ("embaralhando", "pronto", "corrida"):
                self.camera_setas()
            self.atualizar(dt)
            self.desenhar()
            pygame.display.flip()


if __name__ == "__main__":
    Jogo().rodar()