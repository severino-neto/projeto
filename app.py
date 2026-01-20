import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Completo: ENEM e PIB", layout="wide")

# --- CARREGAMENTO E MAPEAMENTO ---
@st.cache_data
def load_data():
    return pd.read_csv('dashboard.csv')

df = load_data()
mapa_dep = {1: "Federal", 2: "Estadual", 3: "Municipal"}

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Pesquisa")

# 1. Filtro por Municípios
todos_muns = sorted(df['NOME_MUNICIPIO'].unique())
selected_muns = st.sidebar.multiselect("Selecione os Municípios", todos_muns)

# 2. Filtro de Ano
anos = sorted(df['ANO'].unique())
selected_years = st.sidebar.multiselect("Anos", anos, default=anos)

# 3. Filtro de Dependência
opcoes_nomes = [mapa_dep[id] for id in sorted(df['DEPENDENCIA_ADM'].unique())]
selected_deps_nomes = st.sidebar.multiselect("Dependência Administrativa", opcoes_nomes, default=opcoes_nomes)
selected_deps_ids = [id for id, nome in mapa_dep.items() if nome in selected_deps_nomes]

# 4. Sliders Numéricos
st.sidebar.subheader("Intervalos de Valores")
s_enem = st.sidebar.slider("Média ENEM", float(df['MED_ENEM'].min()), float(df['MED_ENEM'].max()), (float(df['MED_ENEM'].min()), float(df['MED_ENEM'].max())))
s_pib = st.sidebar.slider("PIB Município", float(df['PIB_MUNICIPIO'].min()), float(df['PIB_MUNICIPIO'].max()), (float(df['PIB_MUNICIPIO'].min()), float(df['PIB_MUNICIPIO'].max())))
s_pc = st.sidebar.slider("PIB Per Capita", float(df['PIB_PER_CAPITA'].min()), float(df['PIB_PER_CAPITA'].max()), (float(df['PIB_PER_CAPITA'].min()), float(df['PIB_PER_CAPITA'].max())))

# --- APLICAÇÃO DOS FILTROS ---
mask = (
    (df['ANO'].isin(selected_years)) &
    (df['DEPENDENCIA_ADM'].isin(selected_deps_ids)) &
    (df['MED_ENEM'].between(s_enem[0], s_enem[1])) &
    (df['PIB_MUNICIPIO'].between(s_pib[0], s_pib[1])) &
    (df['PIB_PER_CAPITA'].between(s_pc[0], s_pc[1]))
)
df_filtered = df[mask].copy()

if selected_muns:
    df_filtered = df_filtered[df_filtered['NOME_MUNICIPIO'].isin(selected_muns)]

df_filtered['NOME_DEP_ADM'] = df_filtered['DEPENDENCIA_ADM'].map(mapa_dep)

# --- FUNÇÃO PARA CRIAR GRÁFICOS SEM QUEBRAR ---
def safe_scatter(data, x, y, title, trendline_type="ols"):
    """Tenta criar gráfico com linha de tendência, se der erro de biblioteca, cria sem ela."""
    try:
        return px.scatter(data, x=x, y=y, color="NOME_DEP_ADM", 
                          hover_name="NOME_MUNICIPIO", trendline=trendline_type,
                          title=title, template="plotly_white")
    except Exception:
        return px.scatter(data, x=x, y=y, color="NOME_DEP_ADM", 
                          hover_name="NOME_MUNICIPIO", trendline=None,
                          title=title + " (Tendência Oculta por Erro de Biblioteca)", 
                          template="plotly_white")

# --- DASHBOARD PRINCIPAL ---
st.title("📊 Painel Integrado: Educação e Indicadores Econômicos")

if not df_filtered.empty:
    # 1. MÉTRICAS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Municípios", len(df_filtered['NOME_MUNICIPIO'].unique()))
    m2.metric("Média ENEM", round(df_filtered['MED_ENEM'].mean(), 1))
    m3.metric("PIB Médio", f"R$ {df_filtered['PIB_MUNICIPIO'].mean():,.0f}")
    
    # Cálculo manual da correlação para não depender do statsmodels
    corr = df_filtered['PIB_PER_CAPITA'].corr(df_filtered['MED_ENEM'])
    m4.metric("Correlação (R)", round(corr, 2) if not pd.isna(corr) else "N/A")

    st.divider()

    # 2. GRÁFICOS DE CORRELAÇÃO (DISPERSÃO) - OS NOVOS
    st.subheader("🎯 Análise de Correlação")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pib = safe_scatter(df_filtered, "PIB_MUNICIPIO", "MED_ENEM", "PIB Município vs ENEM")
        st.plotly_chart(fig_pib, use_container_width=True)

    with col2:
        fig_pc = safe_scatter(df_filtered, "PIB_PER_CAPITA", "MED_ENEM", "PIB Per Capita vs ENEM")
        st.plotly_chart(fig_pc, use_container_width=True)

    st.divider()

    # 3. GRÁFICOS DE COMPARAÇÃO - OS QUE EXISTIAM ANTES
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏫 Média por Dependência")
        resumo_dep = df_filtered.groupby('NOME_DEP_ADM')['MED_ENEM'].mean().reset_index()
        fig_bar = px.bar(resumo_dep, x='NOME_DEP_ADM', y='MED_ENEM', color='NOME_DEP_ADM',
                         labels={'MED_ENEM': 'Média ENEM', 'NOME_DEP_ADM': 'Tipo de Escola'},
                         title="Média ENEM por Gestão")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col4:
        st.subheader("🏆 Top 10 Municípios (Maior Média)")
        top_10 = df_filtered.nlargest(10, 'MED_ENEM')[['NOME_MUNICIPIO', 'MED_ENEM', 'ANO', 'NOME_DEP_ADM']]
        st.dataframe(top_10, use_container_width=True, hide_index=True)

    # 4. TABELA DE DADOS
    st.divider()
    st.subheader("📄 Base de Dados Filtrada")
    st.dataframe(df_filtered.drop(columns=['DEPENDENCIA_ADM']), use_container_width=True)
else:
    st.error("Nenhum dado encontrado para os filtros selecionados.")