import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

RUTA_HISTORICO = "datos/historico_clima.csv"
RUTA_GRAFICO = "salidas/grafico_historico.png"

# Ciudades a graficar (puedes cambiarlas)
CIUDADES_DESTACADAS = ["Santiago", "Concepción", "Antofagasta", "Punta Arenas"]

def cargar_historico(ruta):
    df = pd.read_csv(ruta)
    df["fecha_consulta"] = pd.to_datetime(df["fecha_consulta"])
    print(f"✅ {len(df)} registros cargados del histórico")
    return df

def graficar(df, ciudades, ruta):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for ciudad in ciudades:
        subset = df[df["ciudad"] == ciudad].sort_values("fecha_consulta")
        if subset.empty:
            print(f"⚠️  Sin datos para {ciudad}")
            continue

        axes[0].plot(subset["fecha_consulta"], subset["pm25_valor"],
                     marker="o", label=ciudad)
        axes[1].plot(subset["fecha_consulta"], subset["temp_valor"],
                     marker="o", label=ciudad)

    # Línea de alerta PM2.5
    axes[0].axhline(y=20, color="red", linestyle="--", alpha=0.5,
                    label="Umbral PM2.5 (20 µg/m³)")

    axes[0].set_ylabel("PM2.5 (µg/m³)")
    axes[0].set_title("Evolución del PM2.5 por ciudad")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].set_ylabel("Temperatura (°C)")
    axes[1].set_xlabel("Fecha")
    axes[1].set_title("Evolución de la temperatura por ciudad")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ruta, dpi=100)
    print(f"📊 Gráfico guardado en: {ruta}")
    plt.show()

if __name__ == "__main__":
    df = cargar_historico(RUTA_HISTORICO)
    graficar(df, CIUDADES_DESTACADAS, RUTA_GRAFICO)