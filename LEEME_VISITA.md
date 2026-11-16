# Visita del humanoide G1 — demo en simulador

## macOS
1. Si no tenés Python: `brew install python` (o bajalo de python.org).
2. Doble clic en **INICIAR_VISITA.command**.
   - Si macOS lo bloquea ("desarrollador no identificado"): clic derecho → **Abrir** → **Abrir**.
   - O desde la Terminal: `bash INICIAR_VISITA.command`
3. La primera vez instala MuJoCo y la visión por cámara (unos minutos). Después abre la ventana 3D (puede quedar detrás de la
   Terminal) y muestra el menú de casos de uso.
4. La primera vez que uses la cámara, macOS pide permiso: aceptalo para la
   Terminal. Si lo rechazaste: Configuración del Sistema → Privacidad y
   seguridad → Cámara, activá Terminal y volvé a abrirla (Cmd+Q).

## Linux
`bash INICIAR_VISITA.command`

## Windows
Abrí `INICIAR_SIMULADOR.bat` (elegí G1) y después, en otra ventana:
```
python -m pip install -r mi_desarrollo\requirements-extras.txt
python mi_desarrollo\demo_visita.py
```

## Casos de uso del menú
1. Entrada y saludo
2. Saludo al aula: izquierda, centro y derecha
3. Acercarse y dar la mano
4. Cuadrado de 0.40 m
5. Curva: avanza y gira a la vez
6. Baile con movimientos permitidos
7. Piedra, papel o tijera con el teclado
8. Despedida
9. Presentación: se presenta y cuenta lo que sabe hacer
10. Zigzag
11. Figura de ocho
12. Celebración
13. Control manual con el teclado: `w` `a` `s` `d`, `z` `c` al costado, `h` saludar, `m` mano
14. **Piedra, papel o tijera con la cámara**: el robot ve tu mano

Y además:
- t. Toda la secuencia: opciones 1 a 8

Las figuras nuevas son cerradas: el robot termina donde empezó.

## Piedra, papel o tijera con cámara
Mostrá la mano a la cámara. El robot dice "piedra, papel, tijera" y, al
decir "tijera", hacé tu jugada:

- **Piedra**: puño cerrado
- **Papel**: mano abierta
- **Tijera**: índice y medio estirados

En la ventana se ve qué detecta ("Veo: TIJERA"). `q` o `Esc` en la ventana
termina el juego. Si no hay cámara, se juega con el teclado.

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
| `demo_visita.py` | El programa: menú y casos 1 a 8 |
| `habilidades.py` | Habilidades nuevas y control manual |
| `juego_ppt.py` | Piedra, papel o tijera (teclado o cámara) |
| `vision_ppt.py` | Cámara: detecta la mano con MediaPipe |
| `utilidades.py` | Moverse en metros/grados y hablar |

El registro del simulador queda en `simulador.log`.
