# Visita del humanoide G1 — demo en simulador

## macOS
1. Si no tenés Python: `brew install python` (o bajalo de python.org).
2. Doble clic en **INICIAR_VISITA.command**.
   - Si macOS lo bloquea ("desarrollador no identificado"): clic derecho → **Abrir** → **Abrir**.
   - O desde la Terminal: `bash INICIAR_VISITA.command`
3. La primera vez instala MuJoCo, el control por voz y la visión por cámara
   (unos minutos). Después abre la ventana 3D (puede quedar detrás de la
   Terminal) y muestra el menú de casos de uso.
4. La primera vez que uses la voz o la cámara, macOS pide permiso para el
   **micrófono** / la **cámara**: aceptalo para la Terminal. Si lo rechazaste:
   Configuración del Sistema → Privacidad y seguridad → Micrófono / Cámara.

## Linux
`bash INICIAR_VISITA.command`
(para la voz hace falta PortAudio: `sudo apt install libportaudio2`)

## Windows
Abrí `INICIAR_SIMULADOR.bat` (elegí G1) y después, en otra ventana:
```
python -m pip install -r mi_desarrollo\requirements-extras.txt
python mi_desarrollo\demo_visita.py
```

## Casos de uso del menú
Los de la visita original:
1. Entrada y saludo
2. Saludo al aula (izquierda, centro, derecha)
3. Acercarse y dar la mano
4. Cuadrado de 0.40 m
5. Curva (avanza y gira a la vez)
6. Baile (coreografía con movimientos permitidos)
7. Moonwalk
8. Piedra, papel o tijera con el teclado
9. Despedida

Habilidades nuevas:
10. Presentación (se presenta y cuenta lo que sabe hacer)
11. Zigzag
12. Figura de ocho
13. Cangrejo (pasos al costado)
14. Vigía (mira en las cuatro direcciones)
15. Celebración
16. Control manual con el teclado (`w` `a` `s` `d`, `z` `c` al costado, `h` saludar, `m` mano)
17. **Piedra, papel o tijera con la cámara**: el robot ve tu mano

Y además:
- **v. Hablarle al robot (control por voz)**
- t. Toda la secuencia (1 a 9)

Las figuras nuevas son cerradas: el robot termina donde empezó.

## Control por voz
Elegí `v` en el menú (o arrancá con `bash INICIAR_VISITA.command voz`).
El menú sigue estando: decí **"robot, menú"** (o Ctrl+C) para volver.

Las órdenes empiezan con **"robot"**, así una charla en el aula no lo mueve.
Si decís solo "robot", contesta "¿Sí?" y espera la orden.

| Decí… | Hace |
|---|---|
| robot, avanzá un metro / dos pasos / un poco | camina hacia adelante |
| robot, retrocedé medio metro | camina hacia atrás |
| robot, girá a la izquierda / a la derecha un poco | gira 90° (o 45°) |
| robot, paso al costado a la derecha | se corre sin girar |
| robot, media vuelta / vuelta entera | gira 180° / 360° |
| robot, saludá / saludá a todos / dame la mano | gestos |
| robot, bailá / moonwalk / cuadrado / curva / zigzag / ocho / cangrejo / vigía / festejá / presentate / chau | las coreografías |
| robot, juguemos a piedra, papel o tijera | el juego (con cámara si hay; si no, decís tu jugada) |
| robot, pará | se detiene |
| robot, ayuda | dice qué sabe hacer |

Por seguridad, por voz se mueve **como mucho 1 metro por orden**. Mientras
hace un movimiento no escucha: para frenarlo en el medio, Ctrl+C.

El reconocimiento funciona **sin internet** (Vosk). Solo la primera vez baja
el modelo en español (~40 MB).

## Piedra, papel o tijera con cámara
Mostrá la mano a la cámara. El robot dice "piedra, papel, tijera" y, al
decir "tijera", hacé tu jugada:

- **Piedra**: puño cerrado
- **Papel**: mano abierta
- **Tijera**: índice y medio estirados

En la ventana se ve qué detecta ("Veo: TIJERA"). `q` o `Esc` en la ventana
termina el juego. Si no hay cámara, se juega con el teclado (o de palabra en
el modo voz).

Para probar solo la cámara, sin robot: `python3 mi_desarrollo/vision_ppt.py`

## Seguridad
Todo usa solo los movimientos de la lista blanca (`entorno/sim/acciones.py`):
caminar, girar, saludar y dar la mano, dentro de los límites de la materia.
No hay saltos, acrobacias ni cambios de postura, así que lo que anda en el
simulador anda igual en el robot real.

## Archivos
El código de la demo está en `mi_desarrollo/`:

| Archivo | Para qué |
|---|---|
| `demo_visita.py` | El programa: menú, modo voz y casos 1 a 9 |
| `habilidades.py` | Habilidades nuevas y control manual |
| `juego_ppt.py` | Piedra, papel o tijera (teclado, cámara o voz) |
| `vision_ppt.py` | Cámara: detecta la mano con MediaPipe |
| `voz.py` | Micrófono: entiende órdenes con Vosk |
| `utilidades.py` | Moverse en metros/grados y hablar |

El registro del simulador queda en `simulador.log`.
