import schedule
import time
from datetime import datetime
from robot_clima import main

INTERVALO_MINUTOS = 30  # Cambia aquí si quieres otro intervalo

print("=" * 60)
print("⏰ PROGRAMADOR DE MONITOREO CLIMÁTICO")
print("=" * 60)
print(f"El robot se ejecutará cada {INTERVALO_MINUTOS} minutos.")
print("Presiona Ctrl + C para detenerlo.")
print("=" * 60)

# Ejecutar inmediatamente la primera vez
print(f"\n🚀 Ejecución inicial: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
main()

# Programar ejecuciones futuras
schedule.every(INTERVALO_MINUTOS).minutes.do(main)

# Bucle infinito
while True:
    schedule.run_pending()
    time.sleep(60)