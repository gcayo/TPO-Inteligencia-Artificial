# Visita del humanoide G1 — demo en simulador

## macOS
1. Si no tenés Python: `brew install python` (o bajalo de python.org).
2. Doble clic en **INICIAR_VISITA.command**.
   - Si macOS lo bloquea ("desarrollador no identificado"): clic derecho → **Abrir** → **Abrir**.
   - O desde la Terminal: `bash INICIAR_VISITA.command`
3. La primera vez instala MuJoCo (unos minutos). Después abre la ventana 3D
   (puede quedar detrás de la Terminal) y muestra el menú de casos de uso.

## Linux
`bash INICIAR_VISITA.command`

## Casos de uso del menú
1. Entrada y saludo
2. Saludo al aula (izquierda, centro, derecha)
3. Acercarse y dar la mano
4. Cuadrado de 0.40 m
5. Curva (avanza y gira a la vez)
6. Baile (coreografía con movimientos permitidos)
7. Moonwalk
8. Piedra, papel o tijera (interactivo; en Mac el robot habla)
9. Despedida
t. Toda la secuencia

Para correr todo sin menú: `bash INICIAR_VISITA.command todo`

El código de la demo está en `mi_desarrollo/demo_visita.py`. El registro del
simulador queda en `simulador.log`.
