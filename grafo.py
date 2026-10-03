class ErrorGrafo(Exception):
    pass

class Nodo:

    def __init__(self, id: int, nombre: str, x: float = 0.0, y: float = 0.0):
        self.id = id
        self.nombre = nombre
        self.x = x
        self.y = y

    def etiqueta(self) -> str:
        return self.nombre

    def __repr__(self) -> str:
        return f"Nodo(id={self.id}, nombre={self.nombre!r}, x={self.x:g}, y={self.y:g})"

class Arco:

    def __init__(self, origen: Nodo, destino: Nodo, peso: float):
        self.origen = origen
        self.destino = destino
        self.peso = peso

    def etiqueta(self) -> str:
        return f"{self.origen.nombre}->{self.destino.nombre} ({self.peso:g})"

    def __repr__(self) -> str:
        return f"Arco({self.etiqueta()})"

def validar_peso(valor) -> float:
    try:
        peso = float(valor)
    except (TypeError, ValueError):
        raise ErrorGrafo(
            f"El peso '{valor}' no es un numero valido"
        ) from None

    if peso < 0:
        raise ErrorGrafo(
            f"El peso {peso} es negativo. Dijkstra solo admite pesos no negativos"
        )
    return peso

class Grafo:

    def __init__(self):
        self.nodos: dict[int, Nodo] = {}
        self.arcos: list[Arco] = []
        self._siguiente_id = 1

    def agregar_nodo(self, nombre: str | None = None, x: float = 0.0, y: float = 0.0) -> Nodo:
        if nombre is None or str(nombre).strip() == "":
            nombre = f"N{self._siguiente_id}"
        nombre = str(nombre).strip()

        if any(n.nombre == nombre for n in self.nodos.values()):
            raise ErrorGrafo(f"Ya existe un nodo llamado '{nombre}'.")

        nodo = Nodo(self._siguiente_id, nombre, float(x), float(y))
        self.nodos[nodo.id] = nodo
        self._siguiente_id += 1
        return nodo

    def mover_nodo(self, nodo: Nodo, x: float, y: float) -> None:
        self._exigir_nodo(nodo)
        nodo.x = float(x)
        nodo.y = float(y)

    def eliminar_nodo(self, nodo: Nodo) -> None:
        self._exigir_nodo(nodo)
        self.arcos = [a for a in self.arcos if a.origen is not nodo and a.destino is not nodo]
        del self.nodos[nodo.id]

    def agregar_arco(self, origen: Nodo, destino: Nodo, peso) -> Arco:
        self._exigir_nodo(origen, "origen")
        self._exigir_nodo(destino, "destino")

        if origen is destino:
            raise ErrorGrafo(
                f"No se puede crear un arco de '{origen.nombre}' hacia si mismo."
            )

        peso = validar_peso(peso)

        if self.buscar_arco(origen, destino) is not None:
            raise ErrorGrafo(
                f"Ya existe el arco {origen.nombre}->{destino.nombre}. "
                "Modifique su peso en lugar de duplicarlo."
            )

        arco = Arco(origen, destino, peso)
        self.arcos.append(arco)
        return arco

    def buscar_arco(self, origen: Nodo, destino: Nodo) -> Arco | None:
        for arco in self.arcos:
            if arco.origen is origen and arco.destino is destino:
                return arco
        return None

    def modificar_peso(self, arco: Arco, peso) -> None:
        if arco not in self.arcos:
            raise ErrorGrafo("El arco indicado no pertenece a la red actual.")
        self.buscar_arco(arco.origen, arco.destino).peso = validar_peso(peso)

    def eliminar_arco(self, arco: Arco) -> None:
        if arco not in self.arcos:
            raise ErrorGrafo("El arco indicado no pertenece a la red actual.")
        self.arcos.remove(arco)

    def adyacentes(self, nodo: Nodo) -> list[Arco]:
        return [a for a in self.arcos if a.origen is nodo]

    def incidentes(self, nodo: Nodo) -> list[Arco]:
        return [a for a in self.arcos if a.destino is nodo]

    def nodos_por_nombre(self, nombre: str) -> Nodo | None:
        for nodo in self.nodos.values():
            if nodo.nombre == nombre:
                return nodo
        return None

    def peso_total(self) -> float:
        return sum(a.peso for a in self.arcos)

    def validar_para_dijkstra(self, origen: Nodo | None) -> list[str]:
        problemas: list[str] = []

        if not self.nodos:
            problemas.append("La red no contiene nodos.")
            return problemas

        if len(self.nodos) < 2:
            problemas.append("Se necesitan al menos 2 nodos para aplicar Dijkstra.")

        if not self.arcos:
            problemas.append("La red no contiene arcos.")

        if origen is None:
            problemas.append("No hay un nodo de origen seleccionado.")

        if origen is not None and origen not in self.nodos.values():
            problemas.append("El nodo de origen seleccionado ya no existe en la red.")

        for arco in self.arcos:
            problemas.extend(self._detectar_ciclo(arco))

        return list(dict.fromkeys(problemas))

    def _detectar_ciclo(self, arco: Arco) -> list[str]:
        if arco.peso != 0:
            return []
        if not self._alcanza(arco.destino, arco.origen):
            return []
        return [
            f"Ciclo de peso 0 detectado en {arco.origen.nombre}->{arco.destino.nombre}: "
            "el camino minimo no seria unico."
        ]

    def _alcanza(self, inicio: Nodo, objetivo: Nodo, limite: int = 10_000) -> bool:
        pendientes = [inicio]
        vistos: set[int] = set()
        while pendientes and len(vistos) < limite:
            actual = pendientes.pop()
            if actual is objetivo:
                return True
            if actual.id in vistos:
                continue
            vistos.add(actual.id)
            pendientes.extend(a.destino for a in self.adyacentes(actual))
        return False

    def _exigir_nodo(self, nodo: Nodo, rol: str = "nodo") -> None:
        if not isinstance(nodo, Nodo):
            raise ErrorGrafo(f"El {rol} indicado no es valido.")
        if nodo.id not in self.nodos or self.nodos[nodo.id] is not nodo:
            raise ErrorGrafo(
                f"El {rol} '{getattr(nodo, 'nombre', nodo)}' no existe en la red."
            )

    def limpiar(self) -> None:
        self.nodos.clear()
        self.arcos.clear()
        self._siguiente_id = 1

    def __repr__(self) -> str:
        return f"<Grafo nodos={len(self.nodos)} arcos={len(self.arcos)}>"
