from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
driver = webdriver.Chrome(options=options)

driver.get("https://mantistcy.cl/clima/")

print("⏳ Esperando 8 segundos a que cargue el contenido dinámico...")
time.sleep(8)

print("\n" + "=" * 60)
print("🔎 BÚSQUEDA DE ELEMENTOS CLAVE")
print("=" * 60)

# 1. Buscar todos los elementos que contengan "Estación"
estaciones = driver.find_elements(By.XPATH, "//*[contains(text(), 'Estación')]")
print(f"\n📌 Elementos con texto 'Estación': {len(estaciones)}")
for i, el in enumerate(estaciones[:5]):
    print(f"  [{i}] tag=<{el.tag_name}> class='{el.get_attribute('class')}' texto='{el.text[:60]}'")

# 2. Buscar todos los elementos que contengan "Temp actual"
temps = driver.find_elements(By.XPATH, "//*[contains(text(), 'Temp actual')]")
print(f"\n📌 Elementos con texto 'Temp actual': {len(temps)}")
for i, el in enumerate(temps[:3]):
    print(f"  [{i}] tag=<{el.tag_name}> class='{el.get_attribute('class')}'")
    # Subir al padre para ver el contenedor
    padre = el.find_element(By.XPATH, "..")
    print(f"      Padre: <{padre.tag_name}> class='{padre.get_attribute('class')}'")
    abuelo = padre.find_element(By.XPATH, "..")
    print(f"      Abuelo: <{abuelo.tag_name}> class='{abuelo.get_attribute('class')}'")
    bisabuelo = abuelo.find_element(By.XPATH, "..")
    print(f"      Bisabuelo: <{bisabuelo.tag_name}> class='{bisabuelo.get_attribute('class')}'")

# 3. Contar tarjetas candidatas por clases comunes de Bootstrap
for clase in ["card", "col-6", "rounded", "border-secondary", "bg-dark"]:
    els = driver.find_elements(By.CLASS_NAME, clase)
    print(f"\n📌 Elementos con class='{clase}': {len(els)}")

# 4. Buscar un contenedor de estación completo: probar selector con nombre + temperatura
print("\n" + "=" * 60)
print("🧪 PRUEBA: extraer datos de la primera estación")
print("=" * 60)

# Buscar un elemento que contenga el nombre de una estación conocida
try:
    arica = driver.find_element(By.XPATH, "//*[contains(text(), 'Arica')]")
    print(f"✅ Encontrado 'Arica': <{arica.tag_name}> class='{arica.get_attribute('class')}'")

    # Subir varios niveles para encontrar el contenedor grande
    contenedor = arica
    for nivel in range(1, 6):
        contenedor = contenedor.find_element(By.XPATH, "..")
        clases = contenedor.get_attribute("class") or ""
        print(f"   Nivel {nivel}: <{contenedor.tag_name}> class='{clases[:80]}'")

        # Si encontramos un contenedor con "col" y muchas cosas dentro, paramos
        texto = contenedor.text
        if "Temp actual" in texto and "Humedad" in texto:
            print(f"\n🎯 ¡CONTENEDOR DE ESTACIÓN ENCONTRADO en nivel {nivel}!")
            print(f"   class='{clases}'")
            print(f"   Texto completo:\n{texto}")
            break
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🕵️  Puedes seguir inspeccionando con F12. Tienes 60 segundos.")
time.sleep(60)
driver.quit()