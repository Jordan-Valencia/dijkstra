from __future__ import annotations

from heapq import heappop, heappush
from math import inf
from typing import Iterator

from grafo import Arco, ErrorGrafo, Grafo, Nodo

INF = inf

SELECCION = "seleccion"
ACTUALIZACION = "actualizacion"
INALCANZABLE = "inalcanzable"
FINALIZADO = "finalizado"


def dijkstra(grafo: Grafo, origen: Nodo) -> ResultadoDijkstra:
    problemas = grafo.validar_para_dijkstra(origen)
    if problemas:
        raise ErrorGrafo(" ".join(problemas))

    return ejecutar_dijkstra(grafo, origen)


def ejecutar_dijkstra(grafo: Grafo, origen: Nodo) -> ResultadoDijkstra:
    distancias: dict[int, float] = {n.id: INF for n in grafo.nodos.values()}
    predecesores: dict[int, Nodo | None] = {n.id: None for n in grafo.nodos.values()}
    visited: set[int] = set()

    distancias[origen.id] = 0.0
    monticulo: list[tuple[float, int, Nodo]] = [(0.0, origen.id, origen)]

    while monticulo:
        d_actual, _, nodo_actual = heappop(monticulo)
        if nodo_actual.id in visited:
            continue
        if d_actual > distancias[nodo_actual.id]:
            continue
        visited.add(nodo_actual.id)

        for arco in grafo.adyacentes(nodo_actual):
            if arco.destino.id in visited:
                continue
            d_candidato = d_actual + arco.peso
            if d_candidato < distancias[arco.destino.id]:
                distancias[arco.destino.id] = d_candidato
                predecesores[arco.destino.id] = nodo_actual
                heappush(monticulo, (d_candidato, arco.destino.id, arco.destino))

    return _construir_resultado(grafo, origen, distancias, predecesores)


def _construir_resultado(
    grafo: Grafo,
    origen: Nodo,
    distancias: dict[int, float],
    predecesores: dict[int, Nodo | None],
) -> ResultadoDijkstra:
    arcos_minimos: list[Arco] = []
    for arco in grafo.arcos:
        if (
            predecesores.get(arco.destino.id) is arco.origen
            and abs(distancias[arco.destino.id] - (distancias[arco.origen.id] + arco.peso))
            < 1e-9
        ):
            arcos_minimos.append(arco)

    inalcanzables = [n for n in grafo.nodos.values() if distancias[n.id] == INF]

    return ResultadoDijkstra(
        origen=origen,
        grafo=grafo,
        distancias=dict(distancias),
        predecesores=dict(predecesores),
        arcos_minimos=arcos_minimos,
        inalcanzables=inalcanzables,
    )


def dijkstra_paso_a_paso(grafo: Grafo, origen: Nodo) -> Iterator[Paso]:
    problemas = grafo.validar_para_dijkstra(origen)
    if problemas:
        raise ErrorGrafo(" ".join(problemas))

    distancias: dict[int, float] = {n.id: INF for n in grafo.nodos.values()}
    predecesores: dict[int, Nodo | None] = {n.id: None for n in grafo.nodos.values()}
    visited: set[int] = set()

    distancias[origen.id] = 0.0
    monticulo: list[tuple[float, int, Nodo]] = [(0.0, origen.id, origen)]

    while monticulo:
        d_actual, _, nodo_actual = heappop(monticulo)
        if nodo_actual.id in visited or d_actual > distancias[nodo_actual.id]:
            continue
        visited.add(nodo_actual.id)

        candidatos = sorted(
            (n for n in grafo.nodos.values() if n.id not in visited),
            key=lambda n: distancias[n.id],
        )

        yield Paso(
            tipo=SELECCION,
            nodo=nodo_actual,
            distancia=d_actual,
            candidatos=candidatos[:6],
            texto=(
                f"Visitar {nodo_actual.nombre}: su distancia minima queda "
                f"definitiva en {_fmt(d_actual)}."
            ),
        )

        for arco in grafo.adyacentes(nodo_actual):
            if arco.destino.id in visited:
                continue
            d_candidato = d_actual + arco.peso
            previa = distancias[arco.destino.id]
            if d_candidato < previa:
                distancias[arco.destino.id] = d_candidato
                predecesores[arco.destino.id] = nodo_actual
                heappush(monticulo, (d_candidato, arco.destino.id, arco.destino))
                yield Paso(
                    tipo=ACTUALIZACION,
                    nodo=arco.destino,
                    nodo_origen=nodo_actual,
                    nodo_destino=arco.destino,
                    distancia=d_candidato,
                    distancia_previa=previa,
                    texto=(
                        f"Mejorar {arco.destino.nombre}: "
                        f"{_fmt(previa)} -> {_fmt(d_candidato)} "
                        f"via {nodo_actual.nombre} (peso {arco.peso:g})."
                    ),
                )

    for nodo in grafo.nodos.values():
        if distancias[nodo.id] == INF:
            yield Paso(
                tipo=INALCANZABLE,
                nodo=nodo,
                texto=f"{nodo.nombre} es INALCANZABLE desde {origen.nombre}.",
            )

    resultado = _construir_resultado(grafo, origen, distancias, predecesores)
    resultado.pasos = []

    alcanzables = len(grafo.nodos) - len(resultado.inalcanzables)
    yield Paso(
        tipo=FINALIZADO,
        nodo=origen,
        texto=(
            f"Algoritmo terminado desde {origen.nombre}: {alcanzables} nodo(s) "
            f"alcanzable(s), {len(resultado.inalcanzables)} inalcanzable(s)."
        ),
    )


def _fmt(valor: float) -> str:
    if valor == INF:
        return "inf"
    return f"{valor:g}"


class Paso:

    def __init__(
        self,
        tipo: str,
        nodo: Nodo | None = None,
        nodo_origen: Nodo | None = None,
        nodo_destino: Nodo | None = None,
        distancia: float | None = None,
        distancia_previa: float | None = None,
        candidatos: list[Nodo] | None = None,
        texto: str = "",
    ):
        self.tipo = tipo
        self.nodo = nodo
        self.nodo_origen = nodo_origen
        self.nodo_destino = nodo_destino
        self.distancia = distancia
        self.distancia_previa = distancia_previa
        self.candidatos = [] if candidatos is None else candidatos
        self.texto = texto

    def color(self) -> str:
        return {
            SELECCION: "#1565c0",
            ACTUALIZACION: "#2e7d32",
            INALCANZABLE: "#c62828",
            FINALIZADO: "#37474f",
        }.get(self.tipo, "#37474f")

    def __repr__(self) -> str:
        return f"Paso(tipo={self.tipo!r}, nodo={self.nodo!r}, texto={self.texto!r})"


class ResultadoDijkstra:

    def __init__(
        self,
        origen: Nodo,
        grafo: Grafo | None = None,
        distancias: dict[int, float] | None = None,
        predecesores: dict[int, Nodo | None] | None = None,
        arcos_minimos: list[Arco] | None = None,
        inalcanzables: list[Nodo] | None = None,
        pasos: list[Paso] | None = None,
    ):
        self.origen = origen
        self.grafo = grafo
        self.distancias = {} if distancias is None else distancias
        self.predecesores = {} if predecesores is None else predecesores
        self.arcos_minimos = [] if arcos_minimos is None else arcos_minimos
        self.inalcanzables = [] if inalcanzables is None else inalcanzables
        self.pasos = [] if pasos is None else pasos

    def distancia_de(self, nodo: Nodo) -> float | None:
        valor = self.distancias.get(nodo.id, INF)
        return None if valor == INF else valor

    def es_alcanzable(self, nodo: Nodo) -> bool:
        return self.distancia_de(nodo) is not None

    def camino_a(self, nodo: Nodo) -> list[Nodo]:
        if not self.es_alcanzable(nodo):
            return []
        camino: list[Nodo] = []
        actual: Nodo | None = nodo
        while actual is not None:
            camino.append(actual)
            actual = self.predecesores.get(actual.id)
        camino.reverse()
        return camino

    def arcos_de_camino_a(self, nodo: Nodo) -> list[Arco]:
        camino = self.camino_a(nodo)
        arcos: list[Arco] = []
        for i in range(len(camino) - 1):
            arco = self.buscar_arco(camino[i], camino[i + 1])
            if arco is not None:
                arcos.append(arco)
        return arcos

    def buscar_arco(self, origen: Nodo, destino: Nodo) -> Arco | None:
        if self.grafo is None:
            return None
        return self.grafo.buscar_arco(origen, destino)

    def arcos_totales_minimos(self) -> list[Arco]:
        return list(self.arcos_minimos)

    def __repr__(self) -> str:
        return (
            f"ResultadoDijkstra(origen={self.origen!r}, "
            f"alcanzables={len(self.distancias) - len(self.inalcanzables)}, "
            f"inalcanzables={len(self.inalcanzables)})"
        )