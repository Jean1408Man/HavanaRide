# 🏍️ Havana Ride ❤️

> *Un viaje por las calles de La Habana — contigo, siempre.*

---

## 🎮 El Juego

Conducimos juntos en nuestra moto negra y roja por una calle de La Habana.
Muévete a la izquierda y derecha sobre el asfalto y salta por encima de los
malvados **triciclos**.

En los edificios verás **pancartas** con nuestras frases, mensajes de amor o
fotos de los dos si las colocas dentro de `assets/`. 💕

---

## 🕹️ Controles

| Tecla | Acción |
|-------|--------|
| `←` / `→`  ó  `A` / `D` | Moverse |
| `ESPACIO` / `↑` / `W` | Saltar |
| `ESC` | Menú / Salir |
| `ENTER` | Comenzar / Reintentar |

---

## 🚀 Cómo usarlo en Windows

### Para generar el `.exe` en una PC con Windows
1. Instala **Python 3.9+ (64 bits)** desde [python.org](https://www.python.org/downloads/).
2. Durante la instalación marca la casilla **Add Python to PATH**.
3. Descarga o clona este repositorio en esa PC.
4. Abre la carpeta del proyecto y haz doble click en **`build_windows.bat`**.
5. Espera a que termine el proceso.
6. El ejecutable queda en `dist/HavanaRide.exe`.

### Para llevarlo a otra PC con Windows
1. Copia solo `dist/HavanaRide.exe` a la otra computadora.
2. Haz doble click en ese archivo.
3. No necesitas instalar Python ni nada más en la PC destino.

### Si Windows bloquea el archivo
1. Haz click derecho sobre `HavanaRide.exe`.
2. Elige **Properties / Propiedades**.
3. Si aparece la opción, marca **Unblock / Desbloquear**.
4. Pulsa **Apply / Aplicar** y vuelve a abrir el archivo.

### En Ubuntu/Linux:
```bash
bash build_linux.sh
# Elige opción 1 para ejecutar directo
# O opción 2 para crear un binario de Linux
```

> Nota: desde Linux este script crea un ejecutable para Linux.
> Si quieres un `.exe` de Windows, tienes que compilarlo en Windows con
> `build_windows.bat` o en una máquina/VM con Windows.

---

## 🛠️ Requisitos (solo para build)

- **Python 3.9+** — [python.org](https://www.python.org/downloads/)
- `pip install pygame pyinstaller` (el script lo hace automático)

---

## 📁 Estructura del proyecto

```
havana_ride/
├── main.py              ← Todo el juego (código principal)
├── requirements.txt     ← Dependencias
├── HavanaRide.spec      ← Configuración PyInstaller
├── build_windows.bat    ← Script de build para Windows
├── build_linux.sh       ← Script de build/run para Ubuntu
├── assets/              ← Recursos adicionales (opcional)
└── README.md            ← Este archivo
```

---

## ✏️ Personalizar los mensajes en las pancartas

Abre `main.py` y busca `BILLBOARD_MESSAGES`.
Puedes cambiar los textos por frases reales tuyas:

```python
BILLBOARD_MESSAGES = [
    ("Tu frase aquí", "segunda línea"),
    ("Otra frase bonita", "que dijiste tú"),
    ...
]
```

Para usar fotos, copia imágenes `.png`, `.jpg`, `.jpeg`, `.bmp` o `.webp` dentro
de `assets/`. El juego las recorta automáticamente como pancartas en los
edificios.

---

## ❤️ Con amor

*Hecho con Python + Pygame, todo el código dibujado a mano, sin librerías externas de gráficos.*
*Porque los mejores regalos se hacen desde cero.*
