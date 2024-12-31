import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
import plotly.express as px
from folium.plugins import MarkerCluster
import os

# Configurar el diseño de la página para ser más amplio
st.set_page_config(layout="wide")

# Estilo CSS para un diseño mejorado y fondo personalizado
def inject_custom_css():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("FONDO1.png");
            background-size: cover;
            background-position: center;
            color: white;
        }

        .card_kpi {
            background: rgba(0, 0, 0, 0.8);
            border-radius: 15px;
            border: 2px solid limegreen;
            box-shadow: 2px 2px 12px rgba(0, 255, 0, 0.2);
            padding: 15px;
            text-align: center;
            margin: 5px;
            font-weight: bold;
            color: white;
            transition: all 0.3s ease;
            flex: 1;
            height: 120px;
        }

        .stMarkdown {
            color: white;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

# Llamar a la función CSS
inject_custom_css()

# Configurar la ruta del archivo de datos
current_directory = os.path.dirname(__file__)
data_path = os.path.join(current_directory, "Vista_Detalles_Pedidos_Expanded.csv")

# Leer los datos desde el archivo CSV
try:
    df = pd.read_csv(data_path)
    st.success("Archivo cargado correctamente.")
except FileNotFoundError:
    st.error(f"No se encontró el archivo en la ruta: {data_path}")
    st.stop()
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

# Limpieza y preparación de datos
df['Fecha pedido'] = pd.to_datetime(df['Fecha pedido'], errors='coerce')
df['Latitud_Cliente'].replace([np.inf, -np.inf], np.nan, inplace=True)
df['Longitud_Cliente'].replace([np.inf, -np.inf], np.nan, inplace=True)
df.fillna({"Ingreso Total": 0, "cantidad_vendida": 0, "Total de Pedidos": 0}, inplace=True)
df.dropna(subset=['Latitud_Cliente', 'Longitud_Cliente'], inplace=True)

# Crear KPI Cards
suma_total_pedidos = df["Total de Pedidos"].sum()
suma_cantidad_vendida = df["cantidad_vendida"].sum()
suma_ingresos_totales = df["Ingreso Total"].sum()
suma_costo_total = df["Costo Total"].sum()
suma_margen = df["Margen"].sum()
suma_porcentaje_margen = df["% Margen"].mean()

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"<div class='card_kpi'>📦 Total Pedidos<br><strong>{suma_total_pedidos:,.0f}</strong></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='card_kpi'>📊 Total Cantidad<br><strong>{suma_cantidad_vendida:,.0f}</strong></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='card_kpi'>💰 Ingresos Totales<br><strong>${suma_ingresos_totales:,.2f}</strong></div>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<div class='card_kpi'>💸 Costo Total<br><strong>${suma_costo_total:,.2f}</strong></div>", unsafe_allow_html=True)

with col5:
    st.markdown(f"<div class='card_kpi'>💹 Margen<br><strong>${suma_margen:,.2f}</strong></div>", unsafe_allow_html=True)

with col6:
    st.markdown(f"<div class='card_kpi'>📈 % Margen<br><strong>{suma_porcentaje_margen:,.2f}%</strong></div>", unsafe_allow_html=True)

# Crear gráficos filtrados por cliente, vendedor, distribuidor y producto
with st.expander("Filtro por Cliente y Vendedor"):
    clientes = st.multiselect("Seleccione Clientes", ["Todos"] + list(df['Cliente'].unique()), default="Todos")
    vendedores = st.multiselect("Seleccione Vendedores", ["Todos"] + list(df['Vendedor'].unique()), default="Todos")

filtered_df = df[
    (df['Cliente'].isin(clientes if "Todos" not in clientes else df['Cliente'].unique())) &
    (df['Vendedor'].isin(vendedores if "Todos" not in vendedores else df['Vendedor'].unique()))
]

col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 Ingreso por Cliente")
    ingreso_cliente = filtered_df.groupby("Cliente")["Ingreso Total"].sum().sort_values()
    st.bar_chart(ingreso_cliente)

with col2:
    st.subheader("👤 Ingreso por Vendedor")
    ingreso_vendedor = filtered_df.groupby("Vendedor")["Ingreso Total"].sum().sort_values()
    st.bar_chart(ingreso_vendedor)

# Sección para un mapa interactivo
mapa = folium.Map(location=[4.710989, -74.072092], zoom_start=6)
marker_cluster = MarkerCluster().add_to(mapa)

for _, fila in filtered_df.iterrows():
    tooltip_text = (
        f"<strong>Cliente:</strong> {fila.get('Cliente', 'N/A')}<br>"
        f"<strong>Distribuidor:</strong> {fila.get('Distribuidor', 'N/A')}<br>"
        f"<strong>Ingreso Total:</strong> ${fila.get('Ingreso Total', 0):.2f}"
    )
    folium.Marker(
        location=[fila['Latitud_Cliente'], fila['Longitud_Cliente']],
        tooltip=tooltip_text
    ).add_to(marker_cluster)

st_folium(mapa, width=800, height=500)

# Agregar gráfico circular para estados
if 'estado' in df.columns:
    total_por_estado = df.groupby("estado")["Ingreso Total"].sum()
    fig, ax = plt.subplots()
    colors = ['green', 'orange', 'red'][:len(total_por_estado)]
    ax.pie(total_por_estado, labels=total_por_estado.index, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.set_title("Distribución por Estado")
    st.pyplot(fig)
else:
    st.warning("La columna 'estado' no está presente en los datos.")
