import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from scipy import stats

# Page configuration
st.set_page_config(
    page_title="Análisis Avanzado de Datos de Biogás",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
    .alert-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from Excel file or return None if not found"""
    try:
        df = pd.read_excel("Libro1.xlsx")
        # Convert date columns
        for col in ['dia', 'dia.1', 'dia.2']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Error: No se pudo encontrar el archivo 'Libro1.xlsx'")
        return None
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return None


def create_sample_data():
    """Create sample data for demo purposes"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)
    np.random.seed(42)

    # Create more realistic biogas data with seasonal variations
    seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * np.arange(n_days) / 365.25)

    data = {
        'dia': dates,
        'pome': (np.random.normal(100, 20, n_days) * seasonal_factor).clip(50, 200),
        'dia.1': dates,
        'ch4': np.random.normal(60, 5, n_days).clip(45, 75),
        'co2': np.random.normal(35, 3, n_days).clip(20, 50),
        'h2s': np.random.exponential(0.3, n_days).clip(0.05, 2.0),
        'o2': np.random.exponential(1.5, n_days).clip(0.1, 5.0),
        'dia.2': dates,
        'energia': (np.random.normal(500, 50, n_days) * seasonal_factor).clip(250, 800),
        'teorica': (np.random.normal(550, 40, n_days) * seasonal_factor).clip(300, 850),
        'temperatura': np.random.normal(35, 3, n_days).clip(25, 45),
        'ph': np.random.normal(7.2, 0.3, n_days).clip(6.5, 8.0),
        'presion': np.random.normal(1.5, 0.2, n_days).clip(1.0, 2.5)
    }
    return pd.DataFrame(data)


def calculate_biogas_metrics(df):
    """Calculate advanced biogas production metrics"""
    metrics = {}

    if 'ch4' in df.columns and 'co2' in df.columns:
        # Biogas quality index
        metrics['biogas_quality'] = df['ch4'] / (df['ch4'] + df['co2']) * 100

    if 'pome' in df.columns and 'ch4' in df.columns:
        # Specific methane yield (m³ CH4/m³ POME)
        metrics['specific_yield'] = df['ch4'] * 0.01

    if 'energia' in df.columns and 'teorica' in df.columns:
        # Energy efficiency
        metrics['efficiency'] = (df['energia'] / df['teorica']) * 100

    return metrics


def create_kpi_alerts(df, metrics):
    """Generate KPI-based alerts"""
    alerts = []

    if 'ch4' in df.columns:
        recent_ch4 = df['ch4'].tail(7).mean()
        if recent_ch4 < 50:
            alerts.append("⚠️ Concentración de CH4 por debajo del 50% (últimos 7 días)")
        elif recent_ch4 > 70:
            alerts.append("🟡 Concentración de CH4 muy alta (>70%) - revisar proceso")

    if 'h2s' in df.columns:
        recent_h2s = df['h2s'].tail(7).mean()
        if recent_h2s > 1.0:
            alerts.append("🔴 Concentración de H2S crítica (>1000 ppm)")

    if 'efficiency' in metrics:
        recent_eff = metrics['efficiency'].tail(7).mean()
        if recent_eff < 80:
            alerts.append("📉 Eficiencia energética por debajo del 80%")

    return alerts

# --------------------------------------------------------------
# Helper: scatter with optional trendline (handles missing statsmodels)
# --------------------------------------------------------------

def scatter_with_trendline(df, x_col, y_col, title=""):
    """Return scatter plot with OLS trendline without requiring statsmodels"""
    try:
        import statsmodels.api  # noqa: F401
        fig = px.scatter(df, x=x_col, y=y_col, trendline="ols", title=title)
    except Exception:
        # Fallback using scipy.stats.linregress
        slope, intercept, r_value, p_value, std_err = stats.linregress(df[x_col], df[y_col])
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
        fig.add_trace(go.Scatter(x=df[x_col], y=intercept + slope * df[x_col],
                                 mode="lines", name="OLS"))
    return fig

# Load data

df = load_data()
if df is None:
    st.warning("📁 Usando datos de ejemplo. Carga tu archivo 'Libro1.xlsx' para usar datos reales.")
    df = create_sample_data()

# Calculate advanced metrics
biogas_metrics = calculate_biogas_metrics(df)
for key, value in biogas_metrics.items():
    df[key] = value

# --------------------------------------------------------------
# Main header
# --------------------------------------------------------------

st.markdown("""
<div class="main-header">
    <h1>🌱 Análisis Avanzado de Datos de Biogás</h1>
    <p>Dashboard Integral para Monitoreo y Optimización de Producción</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.header("🔧 Panel de Control")

# Date filtering
date_columns = [col for col in ['dia', 'dia.1', 'dia.2'] if col in df.columns]
if not date_columns:
    st.error("No se encontraron columnas de fecha válidas en los datos")
    st.stop()

min_date = df[date_columns[0]].min().date() if not df[date_columns[0]].isna().all() else datetime.now().date()
max_date = df[date_columns[0]].max().date() if not df[date_columns[0]].isna().all() else datetime.now().date()

start_date = st.sidebar.date_input("📋 Fecha de inicio", min_date)
end_date = st.sidebar.date_input("📋 Fecha de fin", max_date)

if start_date > end_date:
    st.sidebar.error("La fecha de inicio debe ser anterior a la fecha de fin")
    st.stop()

# Filter data
filtered_df = df.copy()
for col in date_columns:
    if col in filtered_df.columns:
        mask = (filtered_df[col] >= pd.to_datetime(start_date)) & (filtered_df[col] <= pd.to_datetime(end_date))
        filtered_df = filtered_df[mask]

# Generate alerts
alerts = create_kpi_alerts(filtered_df, biogas_metrics)

# Display alerts
if alerts:
    st.markdown("### 🚨 Alertas del Sistema")
    for alert in alerts:
        st.markdown(f'<div class="alert-card">{alert}</div>', unsafe_allow_html=True)

# Key Performance Indicators
st.markdown("### 📊 Indicadores Clave de Rendimiento")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if 'pome' in filtered_df.columns:
        total_pome = filtered_df['pome'].sum()
        avg_pome = filtered_df['pome'].mean()
        st.metric("POME Total", f"{total_pome:.0f} m³", f"{avg_pome:.1f} m³/día promedio")

with col2:
    if 'ch4' in filtered_df.columns:
        avg_ch4 = filtered_df['ch4'].mean()
        ch4_trend = filtered_df['ch4'].tail(7).mean() - filtered_df['ch4'].head(7).mean()
        st.metric("CH4 Promedio", f"{avg_ch4:.1f}%", f"{ch4_trend:+.1f}% tendencia")

with col3:
    if 'biogas_quality' in filtered_df.columns:
        quality = filtered_df['biogas_quality'].mean()
        st.metric("Calidad Biogás", f"{quality:.1f}%", "CH4/(CH4+CO2)")

with col4:
    if 'energia' in filtered_df.columns:
        total_energy = filtered_df['energia'].sum()
        st.metric("Energía Total", f"{total_energy:.0f} kWh")

with col5:
    if 'efficiency' in filtered_df.columns:
        avg_efficiency = filtered_df['efficiency'].mean()
        eff_trend = filtered_df['efficiency'].tail(7).mean() - filtered_df['efficiency'].head(7).mean()
        st.metric("Eficiencia", f"{avg_efficiency:.1f}%", f"{eff_trend:+.1f}%")

# --------------------------------------------------------------
# Main visualization tabs
# --------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Tendencias Temporales",
    "⚗️ Composición de Gases",
    "⚡ Análisis Energético",
    "🔗 Correlaciones",
    "📋 Reporte Detallado"
])

# Tab 1: Time trends
with tab1:
    st.subheader("📈 Análisis de Tendencias Temporales")

    if len([col for col in ['pome', 'ch4', 'energia'] if col in filtered_df.columns]) >= 2:
        fig_multi = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Caudal POME (m³/día)', 'Concentración CH4 (%)', 'Energía (kWh)'),
            vertical_spacing=0.08
        )

        if 'pome' in filtered_df.columns and 'dia' in filtered_df.columns:
            fig_multi.add_trace(
                go.Scatter(x=filtered_df['dia'], y=filtered_df['pome'],
                          name='POME', line=dict(color='blue')),
                row=1, col=1
            )

        if 'ch4' in filtered_df.columns and 'dia.1' in filtered_df.columns:
            fig_multi.add_trace(
                go.Scatter(x=filtered_df['dia.1'], y=filtered_df['ch4'],
                          name='CH4', line=dict(color='green')),
                row=2, col=1
            )

        if 'energia' in filtered_df.columns and 'dia.2' in filtered_df.columns:
            fig_multi.add_trace(
                go.Scatter(x=filtered_df['dia.2'], y=filtered_df['energia'],
                          name='Energía', line=dict(color='orange')),
                row=3, col=1
            )

        fig_multi.update_layout(height=800, showlegend=False)
        st.plotly_chart(fig_multi, use_container_width=True)

# Tab 2: Gas composition
with tab2:
    st.subheader("⚗️ Análisis Detallado de Composición de Gases")

    gas_cols = [col for col in ['ch4', 'co2', 'h2s', 'o2'] if col in filtered_df.columns]

    if len(gas_cols) >= 2:
        col_left, col_right = st.columns(2)

        with col_left:
            latest_data = filtered_df[gas_cols].iloc[-1] if len(filtered_df) > 0 else filtered_df[gas_cols].mean()
            fig_pie = px.pie(
                values=latest_data.values,
                names=[col.upper() for col in gas_cols],
                title="Composición Actual del Biogás"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            selected_gases = st.multiselect("Seleccionar gases:", gas_cols, default=gas_cols[:2])

            if selected_gases and 'dia.1' in filtered_df.columns:
                fig_gases = go.Figure()
                for gas in selected_gases:
                    fig_gases.add_trace(go.Scatter(
                        x=filtered_df['dia.1'], y=filtered_df[gas],
                        mode='lines+markers', name=gas.upper()
                    ))
                fig_gases.update_layout(title="Evolución Temporal de Gases",
                                      xaxis_title="Fecha", yaxis_title="Concentración (%)")
                st.plotly_chart(fig_gases, use_container_width=True)

# Tab 3: Energy analysis
with tab3:
    st.subheader("⚡ Análisis Energético Avanzado")

    if 'energia' in filtered_df.columns and 'teorica' in filtered_df.columns:
        col_left, col_right = st.columns(2)

        with col_left:
            fig_energy = go.Figure()
            fig_energy.add_trace(go.Scatter(
                x=filtered_df['dia.2'], y=filtered_df['energia'],
                mode='lines+markers', name='Energía Real', line=dict(color='orange')
            ))
            fig_energy.add_trace(go.Scatter(
                x=filtered_df['dia.2'], y=filtered_df['teorica'],
                mode='lines+markers', name='Energía Teórica', line=dict(color='green')
            ))
            fig_energy.update_layout(title="Comparación Energética",
                                   xaxis_title="Fecha", yaxis_title="Energía (kWh)")
            st.plotly_chart(fig_energy, use_container_width=True)

        with col_right:
            if 'efficiency' in filtered_df.columns:
                fig_hist = px.histogram(filtered_df, x='efficiency', nbins=20,
                                      title="Distribución de Eficiencia Energética")
                fig_hist.add_vline(x=filtered_df['efficiency'].mean(),
                                 line_dash="dash", line_color="red",
                                 annotation_text=f"Promedio: {filtered_df['efficiency'].mean():.1f}%")
                st.plotly_chart(fig_hist, use_container_width=True)

# Tab 4: Correlations
with tab4:
    st.subheader("🔗 Correlaciones")

    if 'pome' in filtered_df.columns and 'energia' in filtered_df.columns:
        fig_scatter1 = scatter_with_trendline(filtered_df, 'pome', 'energia', 'POME vs Energía')
        st.plotly_chart(fig_scatter1, use_container_width=True)

    if 'ch4' in filtered_df.columns and 'co2' in filtered_df.columns:
        fig_scatter2 = scatter_with_trendline(filtered_df, 'ch4', 'co2', 'CH4 vs CO2')
        st.plotly_chart(fig_scatter2, use_container_width=True)

# Tab 5: Detailed Report
with tab5:
    st.subheader("📋 Reporte Detallado")
    st.dataframe(filtered_df)
