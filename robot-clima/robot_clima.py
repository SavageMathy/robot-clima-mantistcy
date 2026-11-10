import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import sys
import io

# Forzar UTF-8 en stdout/stderr (necesario cuando se ejecuta desde n8n/cmd en Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# =========================================================
# CONFIGURACIÓN
# =========================================================
URL = "https://mantistcy.cl/clima/"
RUTA_HISTORICO = "datos/historico_clima.csv"
RUTA_REPORTE = "salidas/reporte_clima.xlsx"
RUTA_ALERTAS = "salidas/alertas_clima.csv"

# Umbrales para alertas
PM25_LIMITE = 20          # µg/m³ (OMS: 15 promedio 24h, usamos 20 como alerta)
TEMP_MAX_ALERTA = 30      # °C
TEMP_MIN_ALERTA = 0       # °C

# =========================================================
# 1. INICIAR NAVEGADOR (VISIBLE)
# =========================================================
def iniciar_navegador():
    options = Options()
    # SIN --headless para que veas la navegación
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

# =========================================================
# 2. EXTRAER DATOS DE CADA ESTACIÓN
# =========================================================
def extraer_estaciones(driver):
    print("⏳ Esperando a que carguen las estaciones...")
    wait = WebDriverWait(driver, 15)

    # Esperar a que aparezca al menos una tarjeta
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bd-card")))

    # Dar un pequeño margen extra para el render dinámico
    time.sleep(3)

    tarjetas = driver.find_elements(By.CLASS_NAME, "bd-card")
    print(f"📌 {len(tarjetas)} tarjetas de estación encontradas")

    estaciones = []

    for tarjeta in tarjetas:
        try:
            datos = extraer_datos_tarjeta(tarjeta)
            if datos:
                estaciones.append(datos)
        except Exception as e:
            print(f"⚠️  Error al procesar una tarjeta: {e}")
            continue

    return estaciones

# =========================================================
# 3. EXTRAER DATOS DE UNA TARJETA INDIVIDUAL
# =========================================================
def extraer_datos_tarjeta(tarjeta):
    datos = {}

    # Nombre de la ciudad (h5)
    try:
        nombre = tarjeta.find_element(By.TAG_NAME, "h5").text.strip()
    except NoSuchElementException:
        return None

    # ✅ FILTRO 1: descartar tarjetas sin nombre o con nombre genérico
    if not nombre or len(nombre) > 40 or "Matriz" in nombre or "Monitoreo" in nombre:
        return None

    # ✅ FILTRO 2: debe tener un span con "Temp actual"
    try:
        tarjeta.find_element(By.XPATH, ".//small[contains(text(), 'Temp actual')]")
    except NoSuchElementException:
        return None  # No es una tarjeta de estación real

    datos["ciudad"] = nombre

    # Tipo de estación (Estación Norte, Centro, Sur)
    try:
        tipo = tarjeta.find_element(
            By.CSS_SELECTOR, "span.text-uppercase"
        ).text.strip()
        datos["zona"] = tipo
    except NoSuchElementException:
        datos["zona"] = "Sin clasificar"

    # Extraer todos los spans "mono fw-bold" (contienen los valores)
    valores = tarjeta.find_elements(By.CSS_SELECTOR, "span.mono.fw-bold")

    # Los valores vienen en orden: Temp actual, Humedad, MP 2.5, (Condición)
    # Pero mejor los asociamos por etiqueta
    campos = tarjeta.find_elements(
        By.CSS_SELECTOR, "small.text-muted-light, span.text-muted-light"
    )

    # Estrategia robusta: buscar por texto de etiqueta
    datos["temperatura"] = buscar_valor_por_etiqueta(tarjeta, "Temp actual")
    datos["humedad"] = buscar_valor_por_etiqueta(tarjeta, "Humedad")
    datos["pm25"] = buscar_valor_por_etiqueta(tarjeta, "MP 2.5")

    # Condición (Nublado, Despejado, etc.)
    try:
        condicion_el = tarjeta.find_element(
            By.XPATH, ".//*[contains(text(), 'Nublado') or contains(text(), 'Despejado') "
                      "or contains(text(), 'Lluvia') or contains(text(), 'Chubascos') "
                      "or contains(text(), 'Parcialmente') or contains(text(), 'Principalmente')]"
        )
        datos["condicion"] = condicion_el.text.strip()
    except NoSuchElementException:
        datos["condicion"] = "No disponible"

    # Extraer Máx, Mín, Lluvia del texto completo de la tarjeta
    texto_completo = tarjeta.text
    datos["temp_max"] = extraer_numero(texto_completo, "Máx:")
    datos["temp_min"] = extraer_numero(texto_completo, "Mín:")
    datos["lluvia_mm"] = extraer_numero(texto_completo, "Lluvia:")

    # Timestamp
    datos["fecha_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return datos

# =========================================================
# 4. HELPERS
# =========================================================
def buscar_valor_por_etiqueta(tarjeta, etiqueta):
    """Busca un <small> con texto = etiqueta y devuelve el valor del span siguiente."""
    try:
        label = tarjeta.find_element(
            By.XPATH, f".//small[contains(text(), '{etiqueta}')]"
        )
        # El valor está en el span hermano siguiente
        contenedor = label.find_element(By.XPATH, "..")
        valor = contenedor.find_element(By.CSS_SELECTOR, "span.mono")
        return valor.text.strip()
    except NoSuchElementException:
        return None

def extraer_numero(texto, prefijo):
    """Extrae el número que sigue a un prefijo como 'Máx:' en un texto."""
    try:
        idx = texto.find(prefijo)
        if idx == -1:
            return None
        fragmento = texto[idx + len(prefijo):].strip()
        # Tomar solo el primer número (puede tener °C, %, mm)
        numero = ""
        for c in fragmento:
            if c.isdigit() or c in ".-":
                numero += c
            elif numero:
                break
        return float(numero) if numero else None
    except Exception:
        return None

# =========================================================
# 5. GENERAR ALERTAS (FOR + IF/ELSE)
# =========================================================
def generar_alertas(df):
    alertas = []

    for _, fila in df.iterrows():
        motivos = []

        # PM2.5 alto
        if fila["pm25_valor"] is not None and fila["pm25_valor"] > PM25_LIMITE:
            motivos.append(f"PM2.5 alto ({fila['pm25_valor']} µg/m³)")

        # Temperatura extrema
        if fila["temp_valor"] is not None:
            if fila["temp_valor"] > TEMP_MAX_ALERTA:
                motivos.append(f"Calor extremo ({fila['temp_valor']}°C)")
            elif fila["temp_valor"] < TEMP_MIN_ALERTA:
                motivos.append(f"Frío extremo ({fila['temp_valor']}°C)")

        if motivos:
            prioridad = "ALTA" if "PM2.5 alto" in " ".join(motivos) else "MEDIA"
            alertas.append({
                "ciudad": fila["ciudad"],
                "zona": fila["zona"],
                "temperatura": fila["temperatura"],
                "pm25": fila["pm25"],
                "motivos": " | ".join(motivos),
                "prioridad": prioridad,
                "fecha_consulta": fila["fecha_consulta"]
            })

    return pd.DataFrame(alertas)

# =========================================================
# 6. GUARDAR HISTÓRICO (ACUMULATIVO)
# =========================================================
def guardar_historico(df, ruta):
    import os
    # Redondear timestamp a minutos para agrupar
    df = df.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_consulta"]).dt.strftime("%Y-%m-%d %H:%M")

    if os.path.exists(ruta):
        historico = pd.read_csv(ruta)
        historico = pd.concat([historico, df], ignore_index=True)
        # Eliminar duplicados: misma ciudad + misma fecha_hora
        historico = historico.drop_duplicates(
            subset=["ciudad", "fecha_hora"], keep="last"
        )
    else:
        historico = df

    historico.to_csv(ruta, index=False)
    print(f"💾 Histórico actualizado: {ruta} ({len(historico)} registros totales)")
    return historico

# =========================================================
# 7. GENERAR REPORTE EXCEL
# =========================================================
def generar_reporte(df, alertas, historico, ruta):
    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Consulta_Actual", index=False)

        if not alertas.empty:
            alertas.to_excel(writer, sheet_name="Alertas", index=False)

        resumen = pd.DataFrame({
            "Métrica": [
                "Total estaciones",
                "PM2.5 promedio",
                "PM2.5 máximo",
                "Temperatura promedio",
                "Temperatura máxima",
                "Temperatura mínima",
                "Total alertas",
                "Registros históricos acumulados",
                "Fecha de consulta"
            ],
            "Valor": [
                len(df),
                round(df["pm25_valor"].mean(), 2) if df["pm25_valor"].notna().any() else "N/A",
                df["pm25_valor"].max() if df["pm25_valor"].notna().any() else "N/A",
                round(df["temp_valor"].mean(), 2) if df["temp_valor"].notna().any() else "N/A",
                df["temp_valor"].max() if df["temp_valor"].notna().any() else "N/A",
                df["temp_valor"].min() if df["temp_valor"].notna().any() else "N/A",
                len(alertas),
                len(historico),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
        })
        resumen.to_excel(writer, sheet_name="Resumen", index=False)

    print(f"📊 Reporte generado: {ruta}")

# =========================================================
# FLUJO PRINCIPAL
# =========================================================
def main():
    print("=" * 60)
    print("🌤️  ROBOT DE MONITOREO CLIMÁTICO - CHILE")
    print("=" * 60)

    driver = iniciar_navegador()

    try:
        print(f"🌐 Navegando a {URL}...")
        driver.get(URL)

        estaciones = extraer_estaciones(driver)
        print(f"✅ {len(estaciones)} estaciones extraídas")

        if not estaciones:
            print("❌ No se extrajeron datos. Revisar selectores.")
            return

        # Convertir a DataFrame
        df = pd.DataFrame(estaciones)

        # Extraer valores numéricos para análisis
        df["temp_valor"] = df["temperatura"].apply(
            lambda x: extraer_numero(x, "") if x else None
        )
        df["pm25_valor"] = df["pm25"].apply(
            lambda x: extraer_numero(x, "") if x else None
        )

        # Mostrar resumen en consola
        print("\n📊 DATOS EXTRAÍDOS")
        print("=" * 60)
        print(df[["zona", "ciudad", "temperatura", "humedad",
                  "pm25", "condicion"]].to_string(index=False))

        # Alertas
        alertas = generar_alertas(df)
        print(f"\n🚨 {len(alertas)} alertas generadas")

        if not alertas.empty:
            print(alertas[["ciudad", "prioridad", "motivos"]].to_string(index=False))
            alertas.to_csv(RUTA_ALERTAS, index=False)

        # Histórico
        historico = guardar_historico(df, RUTA_HISTORICO)

        # Reporte
        generar_reporte(df, alertas, historico, RUTA_REPORTE)

        print("\n" + "=" * 60)
        print("✅ PROCESO FINALIZADO")
        print("=" * 60)
        print("📁 Archivos generados:")
        print(f"   - {RUTA_HISTORICO} (histórico acumulativo)")
        print(f"   - {RUTA_REPORTE}")
        print(f"   - {RUTA_ALERTAS}")

        # Esperar antes de cerrar para que veas el navegador
        print("\n🕵️  El navegador se cerrará en 10 segundos...")
        time.sleep(10)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()