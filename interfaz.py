from __future__ import annotations

import string
import tkinter as tk
from tkinter import ttk

from dijkstra import (
    ACTUALIZACION,
    FINALIZADO,
    INALCANZABLE,
    SELECCION,
    dijkstra,
    dijkstra_paso_a_paso,
)
from grafo import Arco, ErrorGrafo, Grafo, Nodo

FONDO = "#eef1f6"
FONDO_PANEL = "#f8fafc"
CABECERA = "#1e293b"
CABECERA_TXT = "#f8fafc"
TEXTO = "#0f172a"
TEXTO_SUAVE = "#64748b"
BORDE = "#cbd5e1"

LIENZO_FONDO = "#ffffff"
REJILLA = "#eef2f7"

NODO_RELLENO = "#ffffff"
NODO_BORDE = "#334155"
NODO_ORIGEN = "#dc2626"
NODO_ORIGEN_BORDE = "#991b1b"
NODO_INALCANZABLE = "#e2e8f0"
NODO_INALCANZABLE_BORDE = "#94a3b8"

ARCO = "#64748b"
ARCO_MINIMO = "#059669"
ARCO_CONSULTA = "#7c3aed"

ACENTO = "#4f46e5"
ACENTO_HOVER = "#4338ca"
ACENTO_2 = "#0891b2"
ACENTO_2_HOVER = "#0e7490"
PELIGRO = "#dc2626"
PELIGRO_HOVER = "#b91c1c"
NEUTRO = "#475569"
NEUTRO_HOVER = "#334155"

RADIO_NODO = 24
ANCHO_ARCO = 2
ANCHO_ARCO_MIN = 5
SEPARACION_ARCOS = 18
UMBRAL_ARRASTRE = 6
REJILLA_PASO = 28
ZOOM_MIN = 0.35
ZOOM_MAX = 3.0
ZOOM_PASO = 1.2

AYUDA = (
    "Doble clic en area vacia: nuevo nodo\n"
    "Arrastre de un nodo a otro: nuevo arco\n"
    "Doble clic en un nodo: fijar origen\n"
    "Clic en un arco: editar peso\n"
    "Clic derecho: eliminar\n"
    "Rueda del raton: acercar / alejar\n"
    "Flechas: mover nodo   |   Supr: borrar"
)

class AplicacionDijkstra:

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Algoritmo de Dijkstra - Caminos Minimos")
        self.raiz.geometry("1240x800")
        self.raiz.minsize(1040, 660)
        self.raiz.configure(bg=FONDO)

        self.grafo = Grafo()
        self.velocidad = tk.IntVar(value=650)
        self.nombre_origen_manual = tk.StringVar(value="A (doble clic en un nodo)")

        self.nodo_seleccionado: Nodo | None = None
        self.arco_seleccionado: Arco | None = None
        self.nodo_origen: Nodo | None = None
        self.nodo_consulta: Nodo | None = None

        self.resultado = None
        self.nodos_visitados: set[int] = set()
        self._generador = None
        self._id_after = None
        self._animando = False

        self._presionado: Nodo | None = None
        self._origen_arrastre: Nodo | None = None
        self._destino_arrastre: Nodo | None = None
        self._pos_presion = (0, 0)
        self._movido = False
        self._id_previsualizacion = None
        self._origen_pos = None

        self.zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

        self._construir_widgets()
        self._enlazar_eventos()
        self.actualizar_estado()
        self.pintar()

    def _construir_widgets(self) -> None:
        self._ajustar_fuente()
        self._construir_cabecera()

        cuerpo = tk.Frame(self.raiz, bg=FONDO)
        cuerpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._construir_panel(cuerpo)
        self._construir_lienzo(cuerpo)
        self._construir_pie()

    def _ajustar_fuente(self) -> None:
        self.fuente = "Segoe UI"
        self.fuente_mono = "Consolas"

    def _construir_cabecera(self) -> None:
        cabecera = tk.Frame(self.raiz, bg=CABECERA, padx=16, pady=10)
        cabecera.pack(side=tk.TOP, fill=tk.X)

        izquierda = tk.Frame(cabecera, bg=CABECERA)
        izquierda.pack(side=tk.LEFT)

        tk.Label(
            izquierda,
            text="Dijkstra",
            bg=CABECERA,
            fg=CABECERA_TXT,
            font=(self.fuente, 19, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            izquierda,
            text="Caminos minimos desde un origen",
            bg=CABECERA,
            fg="#94a3b8",
            font=(self.fuente, 11),
        ).pack(side=tk.LEFT, padx=(10, 0), pady=6)

        derecha = tk.Frame(cabecera, bg=CABECERA)
        derecha.pack(side=tk.RIGHT)

        self.boton_ejecutar = self._boton(
            derecha, "\u25b6  Ejecutar Dijkstra", self.ejecutar,
            ACENTO, ACENTO_HOVER, "white", grande=True,
        )
        self.boton_paso = self._boton(
            derecha, "\u25b8  Paso a paso", self.ejecutar_paso_a_paso,
            ACENTO_2, ACENTO_2_HOVER, "white", grande=True,
        )
        self.boton_detener = self._boton(
            derecha, "\u25a0  Detener", self.detener_animacion,
            NEUTRO, NEUTRO_HOVER, "white", grande=True,
        )

        franja = tk.Frame(self.raiz, bg="#ffffff", padx=16, pady=7,
                          highlightthickness=1, highlightbackground=BORDE)
        franja.pack(side=tk.TOP, fill=tk.X)

        self.etiqueta_estado = tk.Label(
            franja,
            text="Doble clic en el lienzo para crear tu primer nodo.",
            bg="#ffffff",
            fg=TEXTO,
            font=(self.fuente, 10),
            anchor="w",
        )
        self.etiqueta_estado.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.etiqueta_origen = tk.Label(
            franja, text="ORIGEN:  -", bg="#ffffff", fg=NODO_ORIGEN,
            font=(self.fuente, 10, "bold"), anchor="e", padx=10,
        )
        self.etiqueta_origen.pack(side=tk.RIGHT)

        self.etiqueta_zoom = tk.Label(
            franja, text="Zoom: 100%", bg="#ffffff", fg=TEXTO_SUAVE,
            font=(self.fuente, 9), anchor="e", padx=10,
        )
        self.etiqueta_zoom.pack(side=tk.RIGHT)

    def _boton(self, padre, texto, comando, color=ACENTO, hover=ACENTO_HOVER,
               fg="white", grande=False, fill=tk.NONE, padx=0, pady=0,
               alineacion="center", lado=None, expandir=False):
        marco = tk.Frame(padre, bg=color, cursor="hand2")
        etiqueta = tk.Label(
            marco,
            text=texto,
            bg=color,
            fg=fg,
            font=(self.fuente, 10 if grande else 9, "bold" if grande else "normal"),
            padx=14 if grande else 11,
            pady=8 if grande else 7,
            cursor="hand2",
            anchor=alineacion,
        )
        etiqueta.pack(fill=tk.BOTH, expand=True)
        if lado is not None:
            marco.pack(side=lado, fill=fill, expand=expandir, padx=padx, pady=pady)
        elif fill is not tk.NONE or padx or pady:
            marco.pack(fill=fill, padx=padx, pady=pady)
        else:
            marco.pack(side=tk.LEFT, padx=(0, 8))

        activo = {"on": True}

        def entrar(_evento=None):
            if activo["on"]:
                marco.configure(bg=hover)
                etiqueta.configure(bg=hover)

        def salir(_evento=None):
            if activo["on"]:
                marco.configure(bg=color)
                etiqueta.configure(bg=color)

        def pulsar(_evento=None):
            if activo["on"]:
                marco.configure(bg=hover)
                etiqueta.configure(bg=hover)

        def soltar(_evento=None):
            if activo["on"]:
                salir()
                comando()

        for widget in (marco, etiqueta):
            widget.bind("<Button-1>", pulsar)
            widget.bind("<ButtonRelease-1>", soltar)
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", salir)

        marco._etiqueta = etiqueta
        marco._color = color
        marco._hover = hover
        marco._fg = fg
        marco._activo = activo
        return marco

    def _construir_panel(self, contenedor) -> None:
        marco = tk.Frame(contenedor, bg=BORDE, width=268)
        marco.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1), pady=10)
        marco.pack_propagate(False)

        self._lienzo_panel = tk.Canvas(marco, bg=FONDO_PANEL, highlightthickness=0,
                                       width=266)
        self._scroll_panel = ttk.Scrollbar(marco, orient=tk.VERTICAL,
                                           command=self._lienzo_panel.yview)
        self._scroll_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2))
        self._lienzo_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._lienzo_panel.configure(yscrollcommand=self._scroll_panel.set)

        panel = tk.Frame(self._lienzo_panel, bg=FONDO_PANEL)
        self._ventana_panel = self._lienzo_panel.create_window(
            (0, 0), window=panel, anchor="nw"
        )
        panel.bind(
            "<Configure>",
            lambda _e: self._lienzo_panel.configure(scrollregion=self._lienzo_panel.bbox("all")),
        )
        self._lienzo_panel.bind(
            "<Configure>",
            lambda e: self._lienzo_panel.itemconfigure(self._ventana_panel, width=e.width),
        )

        for widget in (self._lienzo_panel, panel):
            widget.bind("<Enter>", lambda _e: self._activar_rueda(True))
            widget.bind("<Leave>", lambda _e: self._activar_rueda(False))
        self.raiz.bind("<MouseWheel>", self._rueda, add="+")

        self._construir_panel_interior(panel)

    def _activar_rueda(self, activo: bool) -> None:
        self._rueda_activa = activo

    def _rueda(self, evento) -> None:
        if getattr(self, "_rueda_activa", False):
            self._lienzo_panel.yview_scroll(-1 * (evento.delta // 120), "units")

    def _construir_panel_interior(self, panel) -> None:
        def seccion(titulo: str) -> None:
            tk.Frame(panel, bg=BORDE, height=1).pack(fill=tk.X, padx=14, pady=6)
            tk.Label(
                panel, text=titulo.upper(), bg=FONDO_PANEL, fg=TEXTO_SUAVE,
                font=(self.fuente, 8, "bold"), anchor="w",
            ).pack(fill=tk.X, padx=14)

        def boton(texto, comando, color="#ffffff", fg=TEXTO, hover="#e2e8f0"):
            return self._boton(
                panel, texto, comando, color, hover, fg,
                fill=tk.X, padx=14, pady=1, alineacion="w",
            )

        seccion("Nodo de origen")
        self.etiqueta_origen_panel = tk.Label(
            panel, text="Sin seleccionar", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 10, "bold"), anchor="w", wraplength=232,
        )
        self.etiqueta_origen_panel.pack(fill=tk.X, padx=14)

        seccion("Seleccion")
        self.etiqueta_seleccion_panel = tk.Label(
            panel, text="Nada seleccionado", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 9), anchor="w", wraplength=232, justify="left",
        )
        self.etiqueta_seleccion_panel.pack(fill=tk.X, padx=14)

        seccion("Edicion")
        self.boton_fijar_origen = boton("Fijar nodo seleccionado como origen", self.fijar_origen_seleccion)
        self.boton_renombrar = boton("Renombrar nodo", self.renombrar_nodo)
        self.boton_peso = boton("Modificar peso del arco", self.modificar_peso)
        self.boton_eliminar_arco = boton("Eliminar arco", self.eliminar_arco)
        self.boton_eliminar_nodo = boton("Eliminar nodo y sus arcos", self.eliminar_nodo)
        self.boton_quitar_origen = boton("Quitar nodo origen", self.quitar_origen)

        seccion("Animacion")
        marco_velocidad = tk.Frame(panel, bg=FONDO_PANEL)
        marco_velocidad.pack(fill=tk.X, padx=14)
        tk.Label(
            marco_velocidad, text="Lenta", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 8), anchor="w",
        ).pack(side=tk.LEFT)
        tk.Label(
            marco_velocidad, text="Rapida", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 8), anchor="e",
        ).pack(side=tk.RIGHT)
        tk.Scale(
            panel, from_=1400, to=80, orient=tk.HORIZONTAL,
            variable=self.velocidad, length=228, sliderrelief="flat",
            bg=FONDO_PANEL, highlightthickness=0, bd=0,
            command=lambda _v: self.programar_siguiente_paso(),
        ).pack(fill=tk.X, padx=12, pady=6)

        seccion("Vista")
        fila_zoom = tk.Frame(panel, bg=FONDO_PANEL)
        fila_zoom.pack(fill=tk.X, padx=12, pady=1)
        self.boton_zoom_menos = self._boton(
            fila_zoom, "\u2212  Alejar", self.alejar, "#ffffff", "#e2e8f0", TEXTO,
            fill=tk.X, padx=(0, 2), lado=tk.LEFT, expandir=True,
        )
        self.boton_zoom_reset = self._boton(
            fila_zoom, "100%", self.restablecer_zoom, "#ffffff", "#e2e8f0", TEXTO,
            fill=tk.X, padx=2, lado=tk.LEFT, expandir=True,
        )
        self.boton_zoom_mas = self._boton(
            fila_zoom, "Acercar  +", self.acercar, "#ffffff", "#e2e8f0", TEXTO,
            fill=tk.X, padx=(2, 0), lado=tk.LEFT, expandir=True,
        )
        tk.Label(
            panel, text="Rueda del raton sobre el lienzo para acercar o alejar.",
            bg=FONDO_PANEL, fg=TEXTO_SUAVE, font=(self.fuente, 8),
            anchor="w", wraplength=232, justify="left",
        ).pack(fill=tk.X, padx=14, pady=(2, 0))

        seccion("Archivo")
        boton("Ejecutar Dijkstra", self.ejecutar, ACENTO, "white", ACENTO_HOVER)
        boton("Cargar red de ejemplo", self.cargar_ejemplo)
        boton("Exportar resultado (CSV)", self.exportar_csv)
        boton("Nueva red (vaciar)", self.nueva_red, "#ffffff", PELIGRO, "#fee2e2")

        seccion("Ayuda")
        tk.Label(
            panel,
            text=(
                "Doble clic en area vacia: nuevo nodo\n\n"
                "Arrastre de un nodo a otro: nuevo arco\n\n"
                "Doble clic en un nodo: fijar origen\n\n"
                "Clic en un arco: editar peso\n\n"
                "Clic derecho: eliminar\n\n"
                "Rueda del raton: acercar/alejar\n\n"
                "Flechas: mover nodo  |  Supr: borrar"
            ),
            bg=FONDO_PANEL, fg=TEXTO_SUAVE, font=(self.fuente, 8),
            anchor="w", justify="left",
        ).pack(fill=tk.X, padx=14)

    def _construir_lienzo(self, contenedor) -> None:
        marco = tk.Frame(contenedor, bg=BORDE, padx=1, pady=1)
        marco.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)

        self.lienzo = tk.Canvas(marco, bg=LIENZO_FONDO, highlightthickness=0,
                                cursor="crosshair")
        self.lienzo.pack(fill=tk.BOTH, expand=True)
        self.lienzo.bind("<Configure>", lambda _e: self.pintar())

    def _construir_pie(self) -> None:
        pie = tk.Frame(self.raiz, bg=FONDO)
        pie.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=6)

        cuadricula = tk.Frame(pie, bg=FONDO)
        cuadricula.pack(fill=tk.X)
        cuadricula.columnconfigure(0, weight=3, uniform="cols")
        cuadricula.columnconfigure(1, weight=4, uniform="cols")
        cuadricula.columnconfigure(2, weight=3, uniform="cols")

        marco_tabla = tk.Frame(cuadricula, bg="white", highlightthickness=1,
                               highlightbackground=BORDE)
        marco_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tk.Label(
            marco_tabla, text="DISTANCIAS MINIMAS", bg="white", fg=TEXTO_SUAVE,
            font=(self.fuente, 8, "bold"), anchor="w", padx=10, pady=6,
        ).pack(fill=tk.X)

        contenedor_tabla = tk.Frame(marco_tabla, bg="white")
        contenedor_tabla.pack(fill=tk.BOTH, expand=True, padx=(4, 4), pady=6)
        barra = ttk.Scrollbar(contenedor_tabla, orient=tk.VERTICAL)
        self.tabla_distancias = ttk.Treeview(
            contenedor_tabla, columns=("nodo", "distancia", "estado"),
            show="headings", height=5, yscrollcommand=barra.set,
        )
        barra.config(command=self.tabla_distancias.yview)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla_distancias.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for clave, texto, ancho, alineacion in (
            ("nodo", "Nodo", 70, tk.W),
            ("distancia", "Distancia", 80, tk.E),
            ("estado", "Camino minimo", 150, tk.W),
        ):
            self.tabla_distancias.heading(clave, text=texto)
            self.tabla_distancias.column(clave, width=ancho, anchor=alineacion,
                                         stretch=clave == "estado")

        self.tabla_distancias.tag_configure("inalcanzable", foreground=NODO_ORIGEN)
        self.tabla_distancias.tag_configure("origen", foreground=NODO_ORIGEN)
        self.tabla_distancias.tag_configure("minimo", foreground=ARCO_MINIMO)
        self.tabla_distancias.bind("<<TreeviewSelect>>", self.al_seleccionar_fila)

        marco_consulta = tk.Frame(cuadricula, bg="white", highlightthickness=1,
                                  highlightbackground=BORDE)
        marco_consulta.grid(row=0, column=1, sticky="nsew", padx=5)
        tk.Label(
            marco_consulta, text="RECORRIDO SELECCIONADO", bg="white", fg=TEXTO_SUAVE,
            font=(self.fuente, 8, "bold"), anchor="w", padx=10, pady=6,
        ).pack(fill=tk.X)
        self.etiqueta_consulta = tk.Label(
            marco_consulta, text="Haga clic en una fila de la izquierda.",
            bg="white", fg=TEXTO_SUAVE, font=(self.fuente, 9),
            anchor="w", justify="left", padx=10, pady=4, wraplength=420,
        )
        self.etiqueta_consulta.pack(fill=tk.BOTH, expand=True)

        marco_bitacora = tk.Frame(cuadricula, bg="white", highlightthickness=1,
                                  highlightbackground=BORDE)
        marco_bitacora.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        tk.Label(
            marco_bitacora, text="BITACORA PASO A PASO", bg="white", fg=TEXTO_SUAVE,
            font=(self.fuente, 8, "bold"), anchor="w", padx=10, pady=6,
        ).pack(fill=tk.X)
        marco_texto = tk.Frame(marco_bitacora, bg="white")
        marco_texto.pack(fill=tk.BOTH, expand=True, padx=(4, 4), pady=6)
        barra2 = ttk.Scrollbar(marco_texto, orient=tk.VERTICAL)
        self.texto_bitacora = tk.Text(
            marco_texto, bg="#f8fafc", height=5, font=(self.fuente_mono, 9),
            wrap=tk.WORD, state=tk.DISABLED, highlightthickness=0,
            bd=0, padx=6, pady=4,
        )
        barra2.config(command=self.texto_bitacora.yview)
        barra2.pack(side=tk.RIGHT, fill=tk.Y)
        self.texto_bitacora.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _enlazar_eventos(self) -> None:
        self.lienzo.bind("<Double-Button-1>", self.doble_clic)
        self.lienzo.bind("<Button-3>", self.clic_derecho)
        self.lienzo.bind("<ButtonPress-1>", self.presionar)
        self.lienzo.bind("<B1-Motion>", self.arrastrar)
        self.lienzo.bind("<ButtonRelease-1>", self.soltar)
        self.lienzo.bind("<Motion>", self.mover_raton)
        self.lienzo.bind("<MouseWheel>", self._rueda_lienzo)
        self.raiz.bind("<Delete>", lambda _e: self.eliminar_seleccion())
        self.raiz.bind("<Escape>", lambda _e: self.detener_animacion())
        for flecha in ("Left", "Right", "Up", "Down"):
            self.raiz.bind(f"<{flecha}>", lambda _e, f=flecha: self.desplazar(f))
        for secuencia in ("<plus>", "<equal>", "<KP_Add>"):
            self.raiz.bind(secuencia, lambda _e: self.acercar())
        for secuencia in ("<minus>", "<KP_Subtract>"):
            self.raiz.bind(secuencia, lambda _e: self.alejar())
        self.raiz.bind("<Key-0>", lambda _e: self.restablecer_zoom())
        self.raiz.protocol("WM_DELETE_WINDOW", self.cerrar)

    def _a_pantalla(self, x, y):
        return (x - self._pan_x) * self.zoom, (y - self._pan_y) * self.zoom

    def _a_modelo(self, x, y):
        return x / self.zoom + self._pan_x, y / self.zoom + self._pan_y

    def _actualizar_zoom_label(self) -> None:
        if hasattr(self, "etiqueta_zoom"):
            self.etiqueta_zoom.config(text=f"Zoom: {round(self.zoom * 100)}%")

    def _reset_vista(self) -> None:
        self.zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._actualizar_zoom_label()

    def _aplicar_zoom(self, nuevo, foco=None) -> None:
        nuevo = max(ZOOM_MIN, min(ZOOM_MAX, nuevo))
        if abs(nuevo - self.zoom) < 1e-9:
            return
        if foco is None:
            foco = (self.lienzo.winfo_width() / 2, self.lienzo.winfo_height() / 2)
        mx, my = self._a_modelo(foco[0], foco[1])
        self.zoom = nuevo
        self._pan_x = mx - foco[0] / self.zoom
        self._pan_y = my - foco[1] / self.zoom
        self._actualizar_zoom_label()
        self.pintar()

    def acercar(self, foco=None) -> None:
        self._aplicar_zoom(self.zoom * ZOOM_PASO, foco)

    def alejar(self, foco=None) -> None:
        self._aplicar_zoom(self.zoom / ZOOM_PASO, foco)

    def restablecer_zoom(self) -> None:
        self._reset_vista()
        self.pintar()

    def _rueda_lienzo(self, evento) -> str:
        factor = ZOOM_PASO if evento.delta > 0 else 1.0 / ZOOM_PASO
        self._aplicar_zoom(self.zoom * factor, (evento.x, evento.y))
        return "break"

    def _pintar_rejilla(self) -> None:
        ancho, alto = self.lienzo.winfo_width(), self.lienzo.winfo_height()
        if ancho < 2 or alto < 2:
            return
        paso = REJILLA_PASO * self.zoom
        if paso < 6:
            return
        x = (-self._pan_x * self.zoom) % paso
        while x < ancho:
            self.lienzo.create_line(x, 0, x, alto, fill=REJILLA)
            x += paso
        y = (-self._pan_y * self.zoom) % paso
        while y < alto:
            self.lienzo.create_line(0, y, ancho, y, fill=REJILLA)
            y += paso

    def _posiciones_arcos(self) -> dict[int, dict[str, float]]:
        posiciones: dict[int, dict[str, float]] = {}
        for arco in self.grafo.arcos:
            ax, ay = arco.origen.x, arco.origen.y
            bx, by = arco.destino.x, arco.destino.y
            dx, dy = bx - ax, by - ay
            largo = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            ux, uy = dx / largo, dy / largo

            inverso = self.grafo.buscar_arco(arco.destino, arco.origen)
            lado = 1 if inverso is None else (1 if id(arco) < id(inverso) else -1)

            recorte = max(min(RADIO_NODO + 3, largo / 2 - 1), 0.0)
            axp, ayp = ax + ux * recorte, ay + uy * recorte
            bxp, byp = bx - ux * recorte, by - uy * recorte

            x_medio = (axp + bxp) / 2 + (-uy) * SEPARACION_ARCOS * lado
            y_medio = (ayp + byp) / 2 + ux * SEPARACION_ARCOS * lado
            posiciones[id(arco)] = {
                "ax": axp, "ay": ayp,
                "bx": bxp, "by": byp,
                "mx": x_medio, "my": y_medio,
            }
        return posiciones

    def pintar(self) -> None:
        self.lienzo.delete("all")
        self._pintar_rejilla()
        posiciones = self._posiciones_arcos()

        consulta_arcos = set()
        if self.resultado is not None and self.nodo_consulta is not None:
            consulta_arcos = {
                id(a) for a in self.resultado.arcos_de_camino_a(self.nodo_consulta)
            }

        minimos = (
            {id(a) for a in self.resultado.arcos_minimos} if self.resultado else set()
        )

        for arco in self.grafo.arcos:
            self._pintar_arco(arco, posiciones[id(arco)],
                              id(arco) in minimos, id(arco) in consulta_arcos)

        inalcanzables = (
            {n.id for n in self.resultado.inalcanzables} if self.resultado else set()
        )
        for nodo in self.grafo.nodos.values():
            self._pintar_nodo(nodo, nodo.id in inalcanzables)

        if self.nodo_consulta is not None and not consulta_arcos:
            self._pintar_anillo_consulta(self.nodo_consulta)
        self._pintar_previsualizacion()

    def _pintar_arco(self, arco, pos, es_minimo: bool, es_consulta: bool) -> None:
        z = self.zoom
        if es_consulta:
            color, ancho = ARCO_CONSULTA, ANCHO_ARCO_MIN + 1
        elif es_minimo:
            color, ancho = ARCO_MINIMO, ANCHO_ARCO_MIN
        elif self.arco_seleccionado is arco:
            color, ancho = TEXTO, ANCHO_ARCO + 2
        else:
            color, ancho = ARCO, ANCHO_ARCO

        ax, ay = self._a_pantalla(pos["ax"], pos["ay"])
        bx, by = self._a_pantalla(pos["bx"], pos["by"])
        self.lienzo.create_line(
            ax, ay, bx, by,
            fill=color, width=max(1, int(round(ancho * z))),
            arrow=tk.LAST,
            arrowshape=(max(1, int(11 * z)), max(1, int(12 * z)), max(1, int(5 * z))),
        )

        mx, my = self._a_pantalla(pos["mx"], pos["my"])
        ancho_caja = max(9.0, 19 * z)
        alto_caja = max(7.0, 10 * z)
        self.lienzo.create_rectangle(
            mx - ancho_caja, my - alto_caja, mx + ancho_caja, my + alto_caja,
            fill="white", outline=color if (es_minimo or es_consulta) else BORDE,
        )
        self.lienzo.create_text(
            mx, my, text=f"{arco.peso:g}", fill=color,
            font=(self.fuente, max(7, round(9 * z)), "bold"),
        )

    def _pintar_nodo(self, nodo: Nodo, inalcanzable: bool = False) -> None:
        z = self.zoom
        x, y = self._a_pantalla(nodo.x, nodo.y)
        r = RADIO_NODO * z
        tag = (f"nodo_{nodo.id}",)

        self.lienzo.create_oval(
            x - r + 2 * z, y - r + 3 * z,
            x + r + 2 * z, y + r + 3 * z,
            fill="#e2e8f0", outline="", tags=tag,
        )

        if nodo is self.nodo_origen:
            relleno, borde, texto = NODO_ORIGEN, NODO_ORIGEN_BORDE, "white"
        elif inalcanzable:
            relleno, borde, texto = NODO_INALCANZABLE, NODO_INALCANZABLE_BORDE, "#64748b"
        else:
            relleno, borde, texto = NODO_RELLENO, NODO_BORDE, TEXTO

        self.lienzo.create_oval(
            x - r, y - r, x + r, y + r,
            fill=relleno, outline=borde, width=max(1, int(round(3 * z))), tags=tag,
        )
        self.lienzo.create_text(
            x, y - 4 * z, text=nodo.nombre, fill=texto,
            font=(self.fuente, max(7, round(11 * z)), "bold"), tags=tag,
        )

        if nodo in (self.nodo_seleccionado, self._origen_arrastre):
            self.lienzo.create_oval(
                x - r - 6 * z, y - r - 6 * z,
                x + r + 6 * z, y + r + 6 * z,
                outline=ACENTO, width=max(1, int(round(2 * z))),
                dash=(max(2, round(5 * z)), max(2, round(3 * z))), tags=tag,
            )

        if nodo is self.nodo_consulta:
            self._pintar_anillo_consulta(nodo)

        if self.resultado is not None:
            distancia = self.resultado.distancia_de(nodo)
            etiqueta = "sin camino" if distancia is None else f"d = {distancia:g}"
            color = NODO_ORIGEN if distancia is None else ARCO_MINIMO
            self.lienzo.create_text(
                x, y + r + 13 * z, text=etiqueta, fill=color,
                font=(self.fuente, max(7, round(9 * z)), "bold"), tags=tag,
            )

    def _pintar_anillo_consulta(self, nodo: Nodo) -> None:
        z = self.zoom
        x, y = self._a_pantalla(nodo.x, nodo.y)
        r = (RADIO_NODO + 4) * z
        self.lienzo.create_oval(
            x - r, y - r, x + r, y + r,
            outline=ARCO_CONSULTA, width=max(1, int(round(3 * z))),
        )

    def _pintar_previsualizacion(self) -> None:
        if self._id_previsualizacion is None or self._origen_arrastre is None:
            return
        self.lienzo.delete(self._id_previsualizacion)
        destino = self._destino_arrastre
        x2, y2 = (destino.x, destino.y) if destino else self._pos_presion_actual
        ox, oy = self._a_pantalla(self._origen_arrastre.x, self._origen_arrastre.y)
        px, py = self._a_pantalla(x2, y2)
        z = self.zoom
        self._id_previsualizacion = self.lienzo.create_line(
            ox, oy, px, py, fill=ACENTO, width=max(1, int(round(2 * z))),
            dash=(max(2, round(6 * z)), max(2, round(4 * z))),
        )

    def nodo_en(self, x: float, y: float) -> Nodo | None:
        for nodo in self.grafo.nodos.values():
            if (nodo.x - x) ** 2 + (nodo.y - y) ** 2 <= (RADIO_NODO + 4) ** 2:
                return nodo
        return None

    def arco_en(self, x: float, y: float, tolerancia: float | None = None) -> Arco | None:
        if tolerancia is None:
            tolerancia = 9.0 / self.zoom
        mejor, mejor_distancia = None, tolerancia
        for arco in self.grafo.arcos:
            distancia = self.distancia_al_segmento(
                x, y, arco.origen.x, arco.origen.y, arco.destino.x, arco.destino.y
            )
            if distancia < mejor_distancia:
                mejor, mejor_distancia = arco, distancia
        return mejor

    @staticmethod
    def distancia_al_segmento(px, py, x1, y1, x2, y2) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** 0.5

    def mover_raton(self, evento) -> None:
        mx, my = self._a_modelo(evento.x, evento.y)
        self._pos_presion_actual = (mx, my)
        if self._origen_arrastre is not None:
            self._destino_arrastre = self.nodo_en(mx, my)
            self._pintar_previsualizacion()

    def presionar(self, evento) -> None:
        if self._animando:
            self.informar("Animacion en curso. Detengala para editar la red.", "error")
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        self._presionado = nodo
        self._origen_arrastre = nodo
        self._origen_pos = (nodo.x, nodo.y) if nodo is not None else None
        self._destino_arrastre = None
        self._pos_presion = (mx, my)
        self._pos_presion_actual = (mx, my)
        self._movido = False

        if nodo is None:
            self.nodo_seleccionado = None
            self.arco_seleccionado = self.arco_en(mx, my)
            self.actualizar_estado()
            self.pintar()

    def arrastrar(self, evento) -> None:
        if self._presionado is None:
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        self._pos_presion_actual = (mx, my)
        if not self._movido:
            alcance = max(
                abs(mx - self._pos_presion[0]), abs(my - self._pos_presion[1])
            )
            if alcance < UMBRAL_ARRASTRE / self.zoom:
                return
            self._movido = True

        destino = self.nodo_en(mx, my)
        self._destino_arrastre = destino
        if destino is not None:
            self._pintar_previsualizacion()
        else:
            self.lienzo.delete(self._id_previsualizacion or "")
            self._id_previsualizacion = None
            self._presionado.x = mx
            self._presionado.y = my
            self.pintar()

    def soltar(self, evento) -> None:
        origen, destino = self._origen_arrastre, self._destino_arrastre
        movido = self._movido
        self._pintar_previsualizacion()
        self.lienzo.delete(self._id_previsualizacion or "")
        self._id_previsualizacion = None
        self._presionado = None
        self._origen_arrastre = None
        self._destino_arrastre = None
        self._movido = False

        if origen is None:
            if not movido and destino is None:
                self.nodo_seleccionado = None
                self.actualizar_estado()
            self.pintar()
            self._origen_pos = None
            return

        if movido and destino is not None and destino is not origen:
            if self._origen_pos is not None:
                origen.x, origen.y = self._origen_pos
            self._origen_pos = None
            self.crear_arco(origen, destino)
            return

        self._origen_pos = None
        if movido:
            self.limpiar_resultados(silencioso=True)
            self.actualizar_estado()
            self.pintar()
            return

        self.nodo_seleccionado = origen
        self.arco_seleccionado = None
        self.actualizar_estado()
        self.pintar()

    def doble_clic(self, evento) -> None:
        if self._animando:
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        if nodo is not None:
            self.fijar_origen(nodo)
            return
        if self.arco_en(mx, my) is not None:
            return
        self.crear_nodo(mx, my)

    def clic_derecho(self, evento) -> None:
        if self._animando:
            self.informar("Animacion en curso. Detengala para editar la red.", "error")
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        if nodo is not None:
            self.eliminar_nodo(nodo)
            return
        arco = self.arco_en(mx, my)
        if arco is not None:
            self.eliminar_arco(arco)

    def desplazar(self, flecha: str) -> None:
        nodo = self.nodo_seleccionado
        if nodo is None or self._animando:
            return
        paso = 8 / self.zoom
        if flecha == "Left":
            nodo.x -= paso
        elif flecha == "Right":
            nodo.x += paso
        elif flecha == "Up":
            nodo.y -= paso
        else:
            nodo.y += paso
        self.limpiar_resultados(silencioso=True)
        self.pintar()

    def _nombre_automatico(self) -> str:
        usados = {n.nombre for n in self.grafo.nodos.values()}
        for letra in string.ascii_uppercase:
            if letra not in usados:
                return letra
        indice = 1
        while True:
            for letra in string.ascii_uppercase:
                candidato = f"{letra}{indice}"
                if candidato not in usados:
                    return candidato
            indice += 1

    def crear_nodo(self, x: float, y: float) -> None:
        try:
            nodo = self.grafo.agregar_nodo(self._nombre_automatico(), x, y)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.nodo_seleccionado = nodo
        self.arco_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo '{nodo.nombre}' creado. Doble clic en el para fijarlo como origen.", "ok")

    def crear_arco(self, origen: Nodo, destino: Nodo) -> None:
        from tkinter import simpledialog

        peso = simpledialog.askstring(
            "Peso del arco",
            f"Peso del arco  {origen.nombre} \u2192 {destino.nombre}\n"
            "(Dijkstra exige un numero >= 0):",
            parent=self.raiz,
        )
        if peso is None:
            self.informar("Creacion de arco cancelada.", "info")
            self.pintar()
            return
        try:
            arco = self.grafo.agregar_arco(origen, destino, peso)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            self.pintar()
            return
        self.arco_seleccionado = arco
        self.nodo_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Arco creado: {arco.etiqueta()}.", "ok")

    def renombrar_nodo(self) -> None:
        from tkinter import simpledialog

        nodo = self.nodo_seleccionado
        if nodo is None:
            self.informar("Seleccione primero un nodo.", "error")
            return
        nombre = simpledialog.askstring(
            "Renombrar nodo", "Nuevo nombre:", initialvalue=nodo.nombre, parent=self.raiz
        )
        if not nombre:
            return
        try:
            nuevo = nombre.strip()
            if nuevo in {n.nombre for n in self.grafo.nodos.values()}:
                raise ErrorGrafo(f"Ya existe un nodo llamado '{nuevo}'.")
            nodo.nombre = nuevo
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo renombrado a '{nodo.nombre}'.", "ok")

    def modificar_peso(self) -> None:
        from tkinter import simpledialog

        arco = self.arco_seleccionado
        if arco is None:
            self.informar("Seleccione primero un arco: haga clic sobre la linea.", "error")
            return
        peso = simpledialog.askstring(
            "Modificar peso",
            f"Nuevo peso del arco  {arco.origen.nombre} \u2192 {arco.destino.nombre}:",
            initialvalue=f"{arco.peso:g}",
            parent=self.raiz,
        )
        if peso is None:
            return
        try:
            self.grafo.modificar_peso(arco, peso)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.limpiar_resultados(silencioso=True)
        self.pintar()
        self.informar(f"Peso actualizado: {arco.etiqueta()}.", "ok")

    def eliminar_arco(self, arco: Arco | None = None) -> None:
        arco = arco or self.arco_seleccionado
        if arco is None:
            self.informar("Seleccione primero un arco: haga clic sobre la linea.", "error")
            return
        etiqueta = arco.etiqueta()
        try:
            self.grafo.eliminar_arco(arco)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.arco_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Arco {etiqueta} eliminado.", "ok")

    def eliminar_nodo(self, nodo: Nodo | None = None) -> None:
        nodo = nodo or self.nodo_seleccionado
        if nodo is None:
            self.informar("Seleccione primero un nodo.", "error")
            return
        nombre = nodo.nombre
        try:
            self.grafo.eliminar_nodo(nodo)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        for atributo in ("nodo_origen", "nodo_consulta", "nodo_seleccionado"):
            if getattr(self, atributo) is nodo:
                setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo '{nombre}' eliminado junto con sus arcos.", "ok")

    def eliminar_seleccion(self) -> None:
        if self.arco_seleccionado is not None:
            self.eliminar_arco()
        elif self.nodo_seleccionado is not None:
            self.eliminar_nodo()

    def fijar_origen(self, nodo: Nodo) -> None:
        self.nodo_origen = nodo
        self.nodo_seleccionado = nodo
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        problemas = self.grafo.validar_para_dijkstra(nodo)
        if problemas:
            self.informar(f"Origen: {nodo.nombre}. Falta " + " ".join(problemas), "error")
        else:
            self.informar(
                f"Nodo origen: {nodo.nombre}. Pulse 'Ejecutar Dijkstra' para calcular.", "ok"
            )

    def fijar_origen_seleccion(self) -> None:
        if self.nodo_seleccionado is None:
            self.informar("Seleccione primero un nodo.", "error")
            return
        self.fijar_origen(self.nodo_seleccionado)

    def quitar_origen(self) -> None:
        self.nodo_origen = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar("Nodo origen deseleccionado.", "info")

    def ejecutar(self) -> None:
        self.detener_animacion()
        try:
            self.resultado = dijkstra(self.grafo, self.nodo_origen)
        except ErrorGrafo as error:
            self.resultado = None
            self.tabla_distancias.delete(*self.tabla_distancias.get_children())
            self.informar(f"No se puede ejecutar Dijkstra: {error}", "error")
            self.pintar()
            return

        self.pintar_tabla(self.resultado)
        self.escribir_bitacora([])
        self.actualizar_estado()
        self.pintar()
        inalcanzables = self.resultado.inalcanzables
        alcanzables = len(self.grafo.nodos) - len(inalcanzables)
        mensaje = (
            f"Dijkstra ejecutado desde '{self.resultado.origen.nombre}':  "
            f"{alcanzables} nodo(s) alcanzable(s), {len(inalcanzables)} inalcanzable(s)."
        )
        if inalcanzables:
            mensaje += "  Sin camino: " + ", ".join(n.nombre for n in inalcanzables) + "."
        self.informar(mensaje, "ok" if not inalcanzables else "error")

    def ejecutar_paso_a_paso(self) -> None:
        self.detener_animacion()
        try:
            generador = dijkstra_paso_a_paso(self.grafo, self.nodo_origen)
            primero = next(generador)
        except StopIteration:
            self.informar("No hay pasos que mostrar.", "info")
            return
        except ErrorGrafo as error:
            self.informar(f"No se puede ejecutar Dijkstra: {error}", "error")
            return

        self.resultado = None
        self.nodos_visitados = set()
        self.nodo_consulta = None
        self._generador = generador
        self._animando = True
        self.escribir_bitacora([])
        self.tabla_distancias.delete(*self.tabla_distancias.get_children())
        self.etiqueta_consulta.config(
            text="Ejecutando paso a paso...", fg=TEXTO_SUAVE, justify="left"
        )
        self.actualizar_estado()
        self.aplicar_paso(primero)
        self.programar_siguiente_paso()

    def detener_animacion(self) -> None:
        self._animando = False
        self._generador = None
        if self._id_after is not None:
            try:
                self.raiz.after_cancel(self._id_after)
            except tk.TclError:
                pass
            self._id_after = None
        self.actualizar_estado()

    def programar_siguiente_paso(self) -> None:
        if not self._animando or self._generador is None:
            return
        if self._id_after is not None:
            try:
                self.raiz.after_cancel(self._id_after)
            except tk.TclError:
                pass
        espera = max(self.velocidad.get(), 40)
        self._id_after = self.raiz.after(espera, self.avanzar_paso)

    def avanzar_paso(self) -> None:
        if not self._animando or self._generador is None:
            return
        try:
            paso = next(self._generador)
        except StopIteration:
            self._animando = False
            self._generador = None
            self.resultado = dijkstra(self.grafo, self.nodo_origen)
            self.pintar_tabla(self.resultado)
            self.pintar()
            self.informar("Animacion finalizada. Resultados completos en pantalla.", "ok")
            self.actualizar_estado()
            return

        self.aplicar_paso(paso)
        self.programar_siguiente_paso()

    def aplicar_paso(self, paso) -> None:
        if paso.nodo is not None:
            self.nodos_visitados.add(paso.nodo.id)
        if paso.tipo == SELECCION:
            self.nodo_consulta = paso.nodo
        elif paso.tipo == ACTUALIZACION and paso.nodo_destino is not None:
            self.nodo_consulta = paso.nodo_destino

        self.pintar_tabla_parcial()
        self.agregar_bitacora(paso)
        self.informar(paso.texto, paso.tipo)
        self.mostrar_consulta()
        self.pintar()

    def pintar_tabla(self, resultado) -> None:
        self.tabla_distancias.delete(*self.tabla_distancias.get_children())
        for nodo in self.grafo.nodos.values():
            distancia = resultado.distancia_de(nodo)
            if nodo is resultado.origen:
                etiqueta, tag = "es el origen", "origen"
            elif distancia is None:
                etiqueta, tag = "INALCANZABLE", "inalcanzable"
            else:
                etiqueta = " \u2192 ".join(
                    n.nombre for n in resultado.camino_a(nodo)
                )
                tag = "minimo"
            self.tabla_distancias.insert(
                "", tk.END, iid=str(nodo.id),
                values=(nodo.nombre,
                        "inf" if distancia is None else f"{distancia:g}",
                        etiqueta),
                tags=(tag,),
            )

    def pintar_tabla_parcial(self) -> None:
        self.tabla_distancias.delete(*self.tabla_distancias.get_children())
        for nodo in self.grafo.nodos.values():
            if self.nodo_origen is not None and nodo is self.nodo_origen:
                valor, etiqueta, tag = "0", "ORIGEN", "origen"
            elif nodo.id in self.nodos_visitados:
                valor, etiqueta, tag = "definitiva", "VISITADO", "minimo"
            else:
                valor, etiqueta, tag = "...", "PENDIENTE", ""
            self.tabla_distancias.insert(
                "", tk.END, iid=str(nodo.id), values=(nodo.nombre, valor, etiqueta),
                tags=(tag,),
            )

    def al_seleccionar_fila(self, _evento) -> None:
        seleccion = self.tabla_distancias.selection()
        if not seleccion:
            return
        try:
            nodo_id = int(seleccion[0])
        except ValueError:
            return
        self.nodo_consulta = self.grafo.nodos.get(nodo_id)
        self.mostrar_consulta()
        self.pintar()

    def mostrar_consulta(self) -> None:
        if self.resultado is None or self.nodo_consulta is None:
            if self.resultado is None:
                return
            self.etiqueta_consulta.config(
                text=f"{self.nodo_consulta.nombre}: sin camino desde el origen.",
                fg=NODO_ORIGEN, justify="left",
            )
            return

        distancia = self.resultado.distancia_de(self.nodo_consulta)
        if distancia is None:
            self.etiqueta_consulta.config(
                text=(
                    f"{self.nodo_consulta.nombre}\n\n"
                    f"INALCANZABLE desde {self.resultado.origen.nombre}."
                ),
                fg=NODO_ORIGEN, justify="left",
            )
            return

        camino = self.resultado.camino_a(self.nodo_consulta)
        pesos = " + ".join(
            f"{self.grafo.buscar_arco(camino[i], camino[i + 1]).peso:g}"
            for i in range(len(camino) - 1)
        ) or "0"
        self.etiqueta_consulta.config(
            text=(
                f"{self.nodo_consulta.nombre}   \u2192   distancia minima {distancia:g}\n\n"
                f"{'  \u2192  '.join(n.nombre for n in camino)}\n\n"
                f"{pesos} = {distancia:g}"
            ),
            fg=ARCO_CONSULTA, justify="left",
        )

    def escribir_bitacora(self, lineas) -> None:
        self.texto_bitacora.config(state=tk.NORMAL)
        self.texto_bitacora.delete("1.0", tk.END)
        for linea in lineas:
            self.texto_bitacora.insert(tk.END, linea + "\n")
        self.texto_bitacora.config(state=tk.DISABLED)

    def agregar_bitacora(self, paso) -> None:
        self.texto_bitacora.config(state=tk.NORMAL)
        self.texto_bitacora.insert(tk.END, paso.texto + "\n")
        self.texto_bitacora.see(tk.END)
        self.texto_bitacora.config(state=tk.DISABLED)

    def limpiar_resultados(self, silencioso: bool = False) -> None:
        self.resultado = None
        self.nodos_visitados = set()
        self.nodo_consulta = None
        self.etiqueta_consulta.config(
            text="Haga clic en una fila de la izquierda para ver su recorrido.",
            fg=TEXTO_SUAVE, justify="left",
        )
        self.tabla_distancias.delete(*self.tabla_distancias.get_children())
        if not silencioso:
            self.escribir_bitacora([])
            self.informar("Resultados limpiados. Edite la red y vuelva a ejecutar.", "info")
        self.actualizar_estado()

    def nueva_red(self) -> None:
        from tkinter import messagebox

        if self.grafo.nodos and not messagebox.askyesno(
            "Nueva red", "Se eliminara la red actual. Continuar?"
        ):
            return
        self.detener_animacion()
        self.grafo.limpiar()
        self._reset_vista()
        for atributo in ("nodo_origen", "nodo_seleccionado", "arco_seleccionado",
                         "nodo_consulta"):
            setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.escribir_bitacora([])
        self.actualizar_estado()
        self.pintar()
        self.informar(
            "Lienzo vacio. Doble clic en cualquier punto para crear un nodo.", "info"
        )

    def cargar_ejemplo(self) -> None:
        from tkinter import messagebox

        if self.grafo.nodos and not messagebox.askyesno(
            "Red de ejemplo", "Se reemplazara la red actual por el ejemplo. Continuar?"
        ):
            return
        self.detener_animacion()
        self.grafo.limpiar()
        self._reset_vista()
        ancho = max(self.lienzo.winfo_width(), 820)
        alto = max(self.lienzo.winfo_height(), 460)
        cx, cy = ancho / 2, alto / 2
        r = min(ancho * 0.30, alto * 0.38)

        a = self.grafo.agregar_nodo("A", cx - r * 1.5, cy - r * 0.4)
        b = self.grafo.agregar_nodo("B", cx - r * 0.2, cy - r * 1.15)
        c = self.grafo.agregar_nodo("C", cx + r * 1.4, cy - r * 0.3)
        d = self.grafo.agregar_nodo("D", cx + r * 0.8, cy + r * 0.95)
        e = self.grafo.agregar_nodo("E", cx - r * 1.0, cy + r * 0.95)

        self.grafo.agregar_arco(a, b, 4)
        self.grafo.agregar_arco(a, c, 2)
        self.grafo.agregar_arco(b, c, 1)
        self.grafo.agregar_arco(b, d, 5)
        self.grafo.agregar_arco(c, d, 8)
        self.grafo.agregar_arco(c, e, 10)
        self.grafo.agregar_arco(d, e, 3)

        self.nodo_origen = a
        for atributo in ("nodo_seleccionado", "arco_seleccionado", "nodo_consulta"):
            setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.escribir_bitacora([])
        self.actualizar_estado()
        self.pintar()
        self.informar(
            "Red de ejemplo cargada (A, B, C, D, E) con origen 'A'. "
            "Pulse 'Ejecutar Dijkstra'.", "ok"
        )

    def exportar_csv(self) -> None:
        from tkinter import filedialog

        if self.resultado is None:
            self.informar("Ejecute Dijkstra antes de exportar.", "error")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar resultado", defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
        )
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            archivo.write("origen,nodo,distancia_minima,camino_minimo,estado\n")
            for nodo in self.grafo.nodos.values():
                distancia = self.resultado.distancia_de(nodo)
                camino = (
                    " -> ".join(n.nombre for n in self.resultado.camino_a(nodo))
                    if distancia is not None else ""
                )
                if nodo is self.resultado.origen:
                    estado = "origen"
                elif distancia is None:
                    estado = "inalcanzable"
                else:
                    estado = "alcanzable"
                valor = "inf" if distancia is None else f"{distancia:g}"
                archivo.write(
                    f"{self.resultado.origen.nombre},{nodo.nombre},"
                    f"{valor},{camino},{estado}\n"
                )
        self.informar(f"Resultado exportado en {ruta}", "ok")

    def actualizar_estado(self) -> None:
        origen = self.nodo_origen.nombre if self.nodo_origen else "-"
        self.etiqueta_origen.config(text=f"ORIGEN:  {origen}")
        self.etiqueta_origen_panel.config(
            text=self.nodo_origen.nombre if self.nodo_origen else "Sin seleccionar",
            fg=NODO_ORIGEN if self.nodo_origen else TEXTO_SUAVE,
        )

        if self.arco_seleccionado is not None:
            texto, color = self.arco_seleccionado.etiqueta(), TEXTO
        elif self.nodo_seleccionado is not None:
            texto, color = f"Nodo {self.nodo_seleccionado.nombre}", TEXTO
        else:
            texto, color = "Nada seleccionado", TEXTO_SUAVE
        self.etiqueta_seleccion_panel.config(text=texto, fg=color)

        animando = self._animando
        self._habilitar(self.boton_ejecutar, not animando)
        self._habilitar(self.boton_paso, not animando)
        self._habilitar(self.boton_detener, animando)

        self._habilitar(self.boton_peso, self.arco_seleccionado is not None)
        self._habilitar(self.boton_eliminar_arco, self.arco_seleccionado is not None)
        self._habilitar(self.boton_eliminar_nodo, self.nodo_seleccionado is not None)
        self._habilitar(self.boton_renombrar, self.nodo_seleccionado is not None)
        self._habilitar(self.boton_fijar_origen, self.nodo_seleccionado is not None)
        self._habilitar(self.boton_quitar_origen, self.nodo_origen is not None)

    def _habilitar(self, marco, activo: bool) -> None:
        marco._activo["on"] = activo
        if activo:
            color, texto = marco._color, marco._fg
        else:
            color, texto = "#e2e8f0", "#94a3b8"
        marco.configure(bg=color, cursor="hand2" if activo else "arrow")
        marco._etiqueta.configure(bg=color, fg=texto,
                                  cursor="hand2" if activo else "arrow")

    def informar(self, mensaje: str, tipo: str = "info") -> None:
        colores = {
            "info": TEXTO,
            "ok": ARCO_MINIMO,
            "error": NODO_ORIGEN,
            SELECCION: ACENTO,
            ACTUALIZACION: ARCO_MINIMO,
            INALCANZABLE: NODO_ORIGEN,
            FINALIZADO: NEUTRO,
        }
        self.etiqueta_estado.config(text=mensaje, fg=colores.get(tipo, TEXTO))

    def cerrar(self) -> None:
        self.detener_animacion()
        self.raiz.destroy()

def main() -> None:
    raiz = tk.Tk()
    AplicacionDijkstra(raiz)
    raiz.mainloop()

if __name__ == "__main__":
    main()
