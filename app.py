import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback

from dados import load_data

# 1. Configuração da Página
st.set_page_config(page_title="Painel Integrado: Auditoria Logística", layout="wide", page_icon="🚀")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #2e4053; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; color: #555555; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO ORGANIZADORA DE TABELAS ---
def organizar_tabela(df_entrada):
    if df_entrada.empty: return df_entrada
    df = df_entrada.copy()
    colunas_prioritarias = ['Cliente', 'Motorista', 'Filial', 'Pedido', 'Quantidade', 'Rota']
    existentes = [c for c in colunas_prioritarias if c in df.columns]
    outras = [c for c in df.columns if c not in existentes and str(c).lower() not in ['tipo_ocorrencia', 'mes']]
    return df[existentes + outras]

try:
    # 2. CARREGAMENTO DOS DADOS
    df_danos_raw, df_faltas_raw, df_uni_raw, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    # --- LIMPEZA E PADRONIZAÇÃO (VACINA) ---
    df_danos_base = df_danos_raw.copy()
    df_faltas_base = df_faltas_raw.copy()
    df_uni_base = df_uni_raw.copy()

    for df_limpo in [df_danos_base, df_faltas_base, df_uni_base]:
        if not df_limpo.empty:
            if 'Quantidade' in df_limpo.columns:
                df_limpo['Quantidade'] = pd.to_numeric(df_limpo['Quantidade'], errors='coerce').fillna(0)
            colunas_texto = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Pedido']
            for col in colunas_texto:
                if col in df_limpo.columns:
                    df_limpo[col] = df_limpo[col].astype(str).str.strip().replace('nan', 'Não Identificado')

    st.title("📦 Sistema de Auditoria Logística e Prevenção de Fraudes")
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("🔍 Filtros de Operação")
        ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12}
        meses = sorted([m for m in df_uni_base["Periodo"].unique() if m in ordem_meses], key=lambda x: ordem_meses[x])
        periodo_sel = st.selectbox("📅 Mês de Referência:", ["Todos"] + meses)
        filial_sel = st.selectbox("🏢 Filial:", ["Todas"] + sorted(df_uni_base["Filial"].unique().tolist()))
        motorista_sel = st.selectbox("🚛 Motorista:", ["Todos"] + sorted(df_uni_base["Motorista"].unique().tolist()))

    # Aplicação dos Filtros
    df_uni = df_uni_base.copy()
    if periodo_sel != "Todos": df_uni = df_uni[df_uni["Periodo"] == periodo_sel]
    if filial_sel != "Todas": df_uni = df_uni[df_uni["Filial"] == filial_sel]
    if motorista_sel != "Todos": df_uni = df_uni[df_uni["Motorista"] == motorista_sel]

    df_danos = df_uni[df_uni["Tipo_Ocorrencia"] == "Dano"]
    df_faltas = df_uni[df_uni["Tipo_Ocorrencia"] == "Falta"]

    # --- ESTRUTURA DE ABAS ---
    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs([
        "🌐 Geral", "📦 Danos", "📉 Faltas", "🎯 Curva ABC", 
        "🔄 Recorrência", "🗺️ Mapa/Rotas", "🕵️ Clientes", "🚨 Fraudes"
    ])

    # ABA 1: VISÃO GERAL
    with aba1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ocorrências Totais", len(df_uni))
        c2.metric("Itens Totais", int(df_uni["Quantidade"].sum()))
        c3.metric("Volume Faltas", int(df_faltas["Quantidade"].sum()))
        c4.metric("Volume Danos", int(df_danos["Quantidade"].sum()))
        
        st.write("---")
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown("**🏆 Top 10 Motoristas (Faltas + Danos)**")
            ranking = df_uni.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
            fig = px.bar(ranking, x='Quantidade', y='Motorista', orientation='h', color='Quantidade', color_continuous_scale='Viridis')
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col_dir:
            st.markdown("**📊 Divisão por Categoria de Produto**")
            cat_rank = df_uni.groupby('Categoria')['Quantidade'].sum().reset_index()
            fig_pie = px.pie(cat_rank, names='Categoria', values='Quantidade', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # ABA 2: DANOS (Ranking de Motoristas Incluído)
    with aba2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🚛 Top 10 Motoristas (Apenas Danos)**")
            rank_d = df_danos.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
            fig_d = px.bar(rank_d, x='Quantidade', y='Motorista', orientation='h', color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig_d, use_container_width=True)
        with col2:
            st.markdown("**🏢 Danos por Filial (Maior para Menor)**")
            fil_d = df_danos.groupby('Filial')['Quantidade'].sum().reset_index().sort_values('Quantidade', ascending=False)
            fig_fil_d = px.bar(fil_d, x='Filial', y='Quantidade', color='Quantidade', color_continuous_scale='Blues')
            fig_fil_d.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_fil_d, use_container_width=True)
        st.dataframe(organizar_tabela(df_danos), use_container_width=True)

    # ABA 3: FALTAS (Ranking de Motoristas Incluído)
    with aba3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🚛 Top 10 Motoristas (Apenas Faltas)**")
            rank_f = df_faltas.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
            fig_f = px.bar(rank_f, x='Quantidade', y='Motorista', orientation='h', color_discrete_sequence=['#d62728'])
            st.plotly_chart(fig_f, use_container_width=True)
        with col2:
            st.markdown("**🏢 Faltas por Filial (Maior para Menor)**")
            fil_f = df_faltas.groupby('Filial')['Quantidade'].sum().reset_index().sort_values('Quantidade', ascending=False)
            fig_fil_f = px.bar(fil_f, x='Filial', y='Quantidade', color='Quantidade', color_continuous_scale='Reds')
            fig_fil_f.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_fil_f, use_container_width=True)
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True)

    # ABA 4: CURVA ABC (Operando)
    with aba4:
        st.subheader("🎯 Classificação ABC por Motorista (Volume de Itens)")
        abc_data = df_uni_base.groupby('Motorista')['Quantidade'].sum().sort_values(ascending=False).reset_index()
        abc_data['SomaAcumulada'] = abc_data['Quantidade'].cumsum()
        abc_data['PercentagemAcumulada'] = 100 * abc_data['SomaAcumulada'] / abc_data['Quantidade'].sum()
        
        def classificar_abc(p):
            if p <= 70: return 'A (Crítico)'
            elif p <= 90: return 'B (Atenção)'
            else: return 'C (Normal)'
            
        abc_data['Classe'] = abc_data['PercentagemAcumulada'].apply(classificar_abc)
        fig_abc = px.bar(abc_data, x='Motorista', y='Quantidade', color='Classe', title="Curva ABC de Ofensores")
        st.plotly_chart(fig_abc, use_container_width=True)
        st.dataframe(abc_data, use_container_width=True)

    # ABA 5: RECORRÊNCIA (Operando)
    with aba5:
        st.subheader("🔄 Histórico Mensal de Ofensores")
        df_hist = df_uni_base.groupby(['Motorista', 'Periodo']).size().reset_index(name='Casos')
        df_pivot = df_hist.pivot_table(index='Motorista', columns='Periodo', values='Casos', fill_value=0)
        
        # Mapa de Calor
        fig_heat = px.imshow(df_pivot.head(20), text_auto=True, color_continuous_scale='YlOrRd', title="Intensidade de Casos por Mês (Top 20)")
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Tabela de Meses com Ocorrência
        recorrencia = df_uni_base.groupby('Motorista')['Periodo'].nunique().sort_values(ascending=False).reset_index()
        recorrencia.columns = ['Motorista', 'Qtd_Meses_Com_Ocorrencia']
        st.markdown("**Motoristas com maior recorrência (aparecem em vários meses):**")
        st.dataframe(recorrencia[recorrencia['Qtd_Meses_Com_Ocorrencia'] > 1], use_container_width=True)

    # ABA 6 E 7: MAPAS E CLIENTES (Simplificados para Estabilidade)
    with aba6: st.info("🗺️ Módulo Geográfico processando coordenadas...")
    with aba7:
        st.subheader("🕵️ Análise de Clientes Reincidentes")
        if 'Cliente' in df_uni_base.columns:
            cli_rec = df_uni_base.groupby('Cliente').size().reset_index(name='Qtd').sort_values('Qtd', ascending=False)
            st.dataframe(cli_rec[cli_rec['Qtd'] > 1], use_container_width=True)

    # ABA 8: MOTOR DE FRAUDES
    with aba8:
        st.subheader("🚨 Dossiê de Alertas Suspeitos")
        # Regra: Itens > 900 ou Clientes com mesmas quantidades repetidas
        f_vol = df_uni_base[df_uni_base['Quantidade'] >= 900].copy()
        f_vol['Motivo'] = 'Volume Crítico'
        
        df_rep = df_uni_base[df_uni_base['Quantidade'] >= 10].groupby(['Cliente', 'Quantidade']).size().reset_index(name='Vezes')
        cli_susp = df_rep[df_rep['Vezes'] > 1]
        f_rep = pd.merge(df_uni_base, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'])
        f_rep['Motivo'] = 'Padrão Repetitivo'
        
        alertas = pd.concat([f_vol, f_rep]).drop_duplicates(subset=['Pedido', 'Motivo'])
        if not alertas.empty:
            st.error(f"⚠️ Detectados {len(alertas)} indícios de irregularidade.")
            st.dataframe(alertas[['Motivo', 'Cliente', 'Pedido', 'Quantidade', 'Motorista', 'Filial']], use_container_width=True)
        else:
            st.success("Nenhum padrão de fraude detectado com os parâmetros atuais.")

except Exception as e:
    st.error(f"Erro Crítico: {e}")
    st.code(traceback.format_exc())
