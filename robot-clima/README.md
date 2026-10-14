# 🌤️ Robot de Monitoreo Climático - Chile

Automatización con Selenium que extrae datos de estaciones meteorológicas de [mantistcy.cl/clima](https://mantistcy.cl/clima/), genera alertas por PM2.5 y temperaturas extremas, y guarda un histórico acumulativo.

## 📋 Requisitos previos

- **Python 3.10+** ([descargar](https://www.python.org/))
- **Git** ([descargar](https://git-scm.com/))
- **Google Chrome** instalado

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio
```bash
git clone https://github.com/SavageMathy/robot-clima-mantistcy.git
cd robot-clima-mantistcy
```

### 2. Crear el entorno virtual
```bash
python -m venv venv
```

### 3. Activar el entorno virtual

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Verificar la instalación
```bash
python prueba_entorno.py
```
Debe imprimir las versiones de todas las librerías sin errores.

## ▶️ Uso

### Ejecutar una vez (navegador visible)
```bash
python robot_clima.py
```

### Ejecutar programado cada 30 minutos
```bash
python programador.py
```

### Generar gráficos históricos
```bash
python graficos.py
```

## 📁 Estructura del proyecto

```
robot-clima/
├── datos/              # CSV históricos (excluidos de Git)
├── salidas/            # Reportes y gráficos (excluidos de Git)
├── venv/               # Entorno virtual (excluido de Git)
├── robot_clima.py      # Robot principal
├── programador.py      # Ejecución automática
├── graficos.py         # Generación de gráficos
├── requirements.txt    # Dependencias
└── README.md
```

## ⚠️ Notas importantes

- **Nunca subir `venv/` a Git.** Cada colaborador crea el suyo.
- **Los archivos en `datos/` y `salidas/` son locales.** No se versionan.
- **Si actualizas dependencias**, regenera `requirements.txt` con:
  ```bash
  pip freeze > requirements.txt
  ```
  Y avisa al equipo para que reinstale con `pip install -r requirements.txt`.

## 🤝 Cómo contribuir

1. Crea una rama nueva: `git checkout -b mi-mejora`
2. Haz tus cambios y pruébalos.
3. Sube la rama: `git push origin mi-mejora`
4. Abre un **Pull Request** en GitHub.