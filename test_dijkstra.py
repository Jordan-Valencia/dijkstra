import unittest
from math import inf

from dijkstra import (
    ACTUALIZACION,
    FINALIZADO,
    INALCANZABLE,
    SELECCION,
    dijkstra,
    dijkstra_paso_a_paso,
    ejecutar_dijkstra,
)
from grafo import ErrorGrafo, Grafo

def red_clasica() -> tuple[Grafo, list]:
    grafo = Grafo()
    a = grafo.agregar_nodo("A", 100, 100)
    b = grafo.agregar_nodo("B", 300, 100)
    c = grafo.agregar_nodo("C", 200, 300)
    d = grafo.agregar_nodo("D", 400, 300)
    grafo.agregar_arco(a, b, 4)
    grafo.agregar_arco(a, c, 2)
    grafo.agregar_arco(b, c, 1)
    grafo.agregar_arco(b, d, 5)
    grafo.agregar_arco(c, d, 8)
    grafo.agregar_arco(c, b, 10)
    return grafo, [a, b, c, d]

class PruebasGrafo(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = Grafo()

    def test_crear_nodos_con_nombre_automatico(self) -> None:
        primero = self.grafo.agregar_nodo()
        segundo = self.grafo.agregar_nodo()
        self.assertEqual(primero.nombre, "N1")
        self.assertEqual(segundo.nombre, "N2")
        self.assertEqual(len(self.grafo.nodos), 2)

    def test_no_permitir_nombres_duplicados(self) -> None:
        self.grafo.agregar_nodo("A")
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_nodo("A")

    def test_no_permitir_arco_entre_nodos_inexistentes(self) -> None:
        a = self.grafo.agregar_nodo("A")
        fantasma = self.grafo.agregar_nodo("B")
        self.grafo.eliminar_nodo(fantasma)
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(a, fantasma, 1)

    def test_no_permitir_peso_negativo(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(a, b, -3)

    def test_no_permitir_peso_no_numerico(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(a, b, "mucho")

    def test_no_permitir_autoloop(self) -> None:
        a = self.grafo.agregar_nodo("A")
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(a, a, 5)

    def test_peso_cero_es_valido(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        arco = self.grafo.agregar_arco(a, b, 0)
        self.assertEqual(arco.peso, 0.0)

    def test_no_permitir_arco_duplicado(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        self.grafo.agregar_arco(a, b, 3)
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(a, b, 7)

    def test_arcos_entre_los_mismos_nodos_son_distintos(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        ida = self.grafo.agregar_arco(a, b, 3)
        vuelta = self.grafo.agregar_arco(b, a, 4)
        self.assertEqual(len(self.grafo.arcos), 2)
        self.assertIsNone(self.grafo.buscar_arco(ida, vuelta))

    def test_modificar_peso(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        arco = self.grafo.agregar_arco(a, b, 3)
        self.grafo.modificar_peso(arco, 9.5)
        self.assertEqual(arco.peso, 9.5)

    def test_modificar_peso_invalido_conserva_el_anterior(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        arco = self.grafo.agregar_arco(a, b, 3)
        with self.assertRaises(ErrorGrafo):
            self.grafo.modificar_peso(arco, -1)
        self.assertEqual(arco.peso, 3.0)

    def test_eliminar_nodo_elimina_sus_arcos(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        c = self.grafo.agregar_nodo("C")
        self.grafo.agregar_arco(a, b, 1)
        self.grafo.agregar_arco(b, c, 2)
        self.grafo.eliminar_nodo(b)
        self.assertEqual(len(self.grafo.nodos), 2)
        self.assertEqual(len(self.grafo.arcos), 0)

    def test_eliminar_arco(self) -> None:
        a = self.grafo.agregar_nodo("A")
        b = self.grafo.agregar_nodo("B")
        arco = self.grafo.agregar_arco(a, b, 1)
        self.grafo.eliminar_arco(arco)
        self.assertEqual(len(self.grafo.arcos), 0)

class PruebasValidacionesDijkstra(unittest.TestCase):
    def test_red_vacia_no_se_puede_ejecutar(self) -> None:
        grafo = Grafo()
        problemas = grafo.validar_para_dijkstra(None)
        self.assertTrue(problemas)

    def test_falta_nodo_origen(self) -> None:
        grafo, (a, b, c, d) = red_clasica()
        self.assertTrue(grafo.validar_para_dijkstra(None))
        self.assertEqual(grafo.validar_para_dijkstra(a), [])

    def test_red_sin_arcos_no_se_puede_ejecutar(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        grafo.agregar_nodo("B")
        problemas = grafo.validar_para_dijkstra(a)
        self.assertTrue(any("arcos" in p for p in problemas))

    def test_ciclo_de_peso_cero_es_reportado(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        grafo.agregar_arco(a, b, 0)
        grafo.agregar_arco(b, a, 0)
        problemas = grafo.validar_para_dijkstra(a)
        self.assertTrue(any("Ciclo" in p for p in problemas))

    def test_ciclo_con_peso_positivo_es_valido(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        grafo.agregar_arco(a, b, 1)
        grafo.agregar_arco(b, a, 1)
        self.assertEqual(grafo.validar_para_dijkstra(a), [])

class PruebasDijkstra(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo, (self.a, self.b, self.c, self.d) = red_clasica()

    def test_distancias_minimas(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        self.assertEqual(resultado.distancia_de(self.a), 0.0)
        self.assertEqual(resultado.distancia_de(self.b), 4.0)
        self.assertEqual(resultado.distancia_de(self.c), 2.0)
        self.assertEqual(resultado.distancia_de(self.d), 9.0)

    def test_camino_minimo_hasta_d(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        camino = [n.nombre for n in resultado.camino_a(self.d)]
        self.assertEqual(camino, ["A", "B", "D"])

    def test_camino_minimo_hasta_c(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        camino = [n.nombre for n in resultado.camino_a(self.c)]
        self.assertEqual(camino, ["A", "C"])

    def test_arcos_minimos_son_los_del_arbol(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        pares = {(a.origen.nombre, a.destino.nombre) for a in resultado.arcos_minimos}
        self.assertEqual(pares, {("A", "B"), ("A", "C"), ("B", "D")})

    def test_origen_tiene_distancia_cero_y_camino_de_un_solo_nodo(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        self.assertEqual([n.nombre for n in resultado.camino_a(self.a)], ["A"])

    def test_suma_de_pesos_del_camino_igual_a_la_distancia(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        for nodo in self.grafo.nodos.values():
            camino = resultado.camino_a(nodo)
            suma = 0.0
            for i in range(len(camino) - 1):
                suma += self.grafo.buscar_arco(camino[i], camino[i + 1]).peso
            self.assertAlmostEqual(suma, resultado.distancia_de(nodo), places=9)

    def test_nodo_inalcanzable(self) -> None:
        self.grafo.agregar_nodo("E", 500, 100)
        resultado = dijkstra(self.grafo, self.a)
        e = self.grafo.nodos_por_nombre("E")
        self.assertIsNone(resultado.distancia_de(e))
        self.assertFalse(resultado.es_alcanzable(e))
        self.assertIn(e, resultado.inalcanzables)
        self.assertEqual(resultado.camino_a(e), [])

    def test_red_ilegible_lanza_error(self) -> None:
        with self.assertRaises(ErrorGrafo):
            dijkstra(self.grafo, None)

    def test_el_nodo_d_no_tiene_arcos_salientes(self) -> None:
        resultado = dijkstra(self.grafo, self.d)
        self.assertEqual(resultado.distancia_de(self.d), 0.0)
        for nodo in (self.a, self.b, self.c):
            self.assertIsNone(resultado.distancia_de(nodo))
        self.assertEqual(len(resultado.inalcanzables), 3)

    def test_camino_desde_c_hasta_b_usa_el_arco_mas_barato(self) -> None:
        resultado = dijkstra(self.grafo, self.c)
        self.assertEqual(resultado.distancia_de(self.b), 10.0)
        self.assertEqual(
            [n.nombre for n in resultado.camino_a(self.b)], ["C", "B"]
        )

    def test_camino_mas_corto_que_la_suma_de_todos_los_arcos(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        self.assertLess(resultado.distancia_de(self.d), self.grafo.peso_total())

    def test_red_de_un_solo_nodo_con_arco_a_si_mismo_no_se_puede_ejecutar(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        grafo.agregar_arco(a, grafo.agregar_nodo("B"), 1)
        grafo.eliminar_nodo(grafo.nodos_por_nombre("B"))
        self.assertTrue(grafo.validar_para_dijkstra(a))

class PruebasDijkstraContraFuerzaBruta(unittest.TestCase):

    def test_coincide_con_bellman_ford(self) -> None:
        import random

        for semilla in range(40):
            aleatorio = random.Random(semilla)
            grafo = Grafo()
            nombres = [f"N{i}" for i in range(aleatorio.randint(2, 7))]
            nodos = [grafo.agregar_nodo(n) for n in nombres]
            for origen in nodos:
                for destino in nodos:
                    if origen is not destino and aleatorio.random() < 0.4:
                        grafo.agregar_arco(
                            origen, destino, aleatorio.randint(0, 30)
                        )
            if not grafo.arcos:
                continue

            origen = aleatorio.choice(nodos)
            resultado = ejecutar_dijkstra(grafo, origen)
            esperado = self._bellman_ford(grafo, origen)

            self.assertEqual(
                set(resultado.distancias.keys()),
                set(esperado.keys()),
                f"semilla {semilla}: nodos distintos",
            )
            for nodo in nodos:
                obtenido = resultado.distancia_de(nodo)
                referencia = esperado[nodo.id]
                if referencia == inf:
                    self.assertIsNone(obtenido, f"semilla {semilla}, {nodo.nombre}")
                else:
                    self.assertAlmostEqual(
                        obtenido, referencia, places=9,
                        msg=f"semilla {semilla}, nodo {nodo.nombre}",
                    )

    @staticmethod
    def _bellman_ford(grafo: Grafo, origen) -> dict[int, float]:
        distancias = {n.id: inf for n in grafo.nodos.values()}
        distancias[origen.id] = 0.0
        for _ in range(len(grafo.nodos) - 1):
            cambio = False
            for arco in grafo.arcos:
                if distancias[arco.origen.id] == inf:
                    continue
                nuevo = distancias[arco.origen.id] + arco.peso
                if nuevo < distancias[arco.destino.id]:
                    distancias[arco.destino.id] = nuevo
                    cambio = True
            if not cambio:
                break
        return distancias

class PruebasPasoAPaso(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo, (self.a, self.b, self.c, self.d) = red_clasica()
        self.pasos = list(dijkstra_paso_a_paso(self.grafo, self.a))

    def test_el_primer_paso_selecciona_el_origen(self) -> None:
        self.assertEqual(self.pasos[0].tipo, SELECCION)
        self.assertIs(self.pasos[0].nodo, self.a)
        self.assertEqual(self.pasos[0].distancia, 0.0)

    def test_el_ultimo_paso_es_finalizado(self) -> None:
        self.assertEqual(self.pasos[-1].tipo, FINALIZADO)

    def test_las_actualizaciones_reportan_mejora_real(self) -> None:
        definitiva: dict[int, float] = {self.a.id: 0.0}
        for paso in self.pasos:
            if paso.tipo == SELECCION:
                definitiva[paso.nodo.id] = paso.distancia
                continue
            if paso.tipo != ACTUALIZACION:
                continue

            arco = self.grafo.buscar_arco(paso.nodo_origen, paso.nodo_destino)
            self.assertIsNotNone(arco)
            self.assertLess(paso.distancia, paso.distancia_previa)
            self.assertAlmostEqual(
                paso.distancia, definitiva[paso.nodo_origen.id] + arco.peso, places=9
            )

    def test_los_pasos_terminan_con_cada_nodo_una_vez(self) -> None:
        visitados = [p.nodo for p in self.pasos if p.tipo == SELECCION]
        self.assertEqual(len(visitados), len(self.grafo.nodos))
        self.assertEqual(len({n.id for n in visitados}), len(self.grafo.nodos))

    def test_paso_a_paso_es_consistente_con_el_resultado_final(self) -> None:
        resultado = dijkstra(self.grafo, self.a)
        for paso in self.pasos:
            if paso.tipo != SELECCION:
                continue
            self.assertAlmostEqual(
                paso.distancia, resultado.distancia_de(paso.nodo), places=9
            )

    def test_reporta_nodos_inalcanzables(self) -> None:
        e = self.grafo.agregar_nodo("E", 500, 100)
        pasos = list(dijkstra_paso_a_paso(self.grafo, self.a))
        inalcanzables = [p for p in pasos if p.tipo == INALCANZABLE]
        self.assertEqual(len(inalcanzables), 1)
        self.assertIs(inalcanzables[0].nodo, e)

    def test_red_invalida_lanza_error(self) -> None:
        with self.assertRaises(ErrorGrafo):
            list(dijkstra_paso_a_paso(self.grafo, None))

if __name__ == "__main__":
    unittest.main(verbosity=2)
