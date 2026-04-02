import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback

from dados import load_data

st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #2e4053; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; color: #555555; }
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] { font-size: 1.5rem; }
        [data-testid="stMetricLabel"] { font-size: 0.9rem; }
        .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.8rem !important; }
    }
</style>
""", unsafe_allow_html=True)

def organizar_tabela(df_entrada):
    if df_entrada.empty:
        return df_entrada
    df = df_entrada.copy()
    
    colunas_iniciais = ['Cliente', 'Motorista', 'Filial', 'Pedido', 'Quantidade', 'Rota']
    colunas_iniciais = [c for c in colunas_iniciais if c in df.columns]
    
    colunas_esconder = ['transportadora', 'nome_transportadora', 'desvio_logistico', 'tipo_ocorrencia', 'mes_limpo', 'mes']
    outras_colunas = [c for c in df.columns if c not in colunas_iniciais and str(c).lower() not in colunas_esconder]
    return df[colunas_iniciais + outras_colunas]

try:
    df_danos_raw, df_faltas_raw, df_uni_raw, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    # VACINA BLINDADA
    df_danos_base = df_danos_raw.copy()
    df_faltas_base = df_faltas_raw.copy()
    df_uni_base = df_uni_raw.copy()

    for df_limpo in [df_danos_base, df_faltas_base, df_uni_base]:
        if not df_limpo.empty:
            if 'Quantidade' in df_limpo.columns:
                df_limpo['Quantidade'] = pd.to_numeric(df_limpo['Quantidade'], errors='coerce').fillna(0)
            
            colunas_texto = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Tipo_Ocorrencia', 'Pedido']
            for col in colunas_texto:
                if col in df_limpo.columns:
                    df_limpo[col] = df_limpo[col].astype(str).str.strip()
                    df_limpo.loc[df_limpo[col] == 'nan', col] = 'Não Identificado'

    st.title("🚀 Painel Integrado e Prevenção de Fraudes")
    st.markdown("Visão consolidada cruzando dados de **Danos**, **Faltas** e **Auditoria Logística**.")
    
    if not df_uni_base.empty:
        total_ocorrencias = len(df_uni_base)
        pior_motorista = df_uni_base['Motorista'].value_counts().idxmax()
        qtd_pior_motorista = df_uni_base['Motorista'].value_counts().max()
        pct_motorista = (qtd_pior_motorista / total_ocorrencias) * 100
        pior_filial = df_uni_base['Filial'].value_counts().idxmax()
        pior_categoria = df_uni_base['Categoria'].value_counts().idxmax()
        
        alerta1, alerta2, alerta3 = st.columns(3)
        with alerta1: st.warning(f"⚠️ **Maior Ofensor:** {pior_motorista} ({pct_motorista:.1f}%).")
        with alerta2: st.error(f"🚨 **Filial Crítica:** {pior_filial} concentra o maior volume.")
        with alerta3: st.info(f"📦 **Categoria Sensível:** {pior_categoria} apresenta maior incidência.")
            
    st.divider()

    with st.sidebar:
        st.header("🔍 Filtros Integrados")
        ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12, 'N/A': 99, 'Não Identificado': 99}
        meses_disponiveis = sorted([str(m) for m in df_uni_base["Periodo"].unique() if str(m) not in ['N/A', 'Não Identificado']], key=lambda x: ordem_meses.get(x, 100))
        periodo_sel = st.selectbox("📅 Escolha o Mês:", ["Todos"] + meses_disponiveis)
        motorista_sel = st.selectbox("🚛 Motorista:", ["Todos"] + sorted([str(x) for x in df_uni_base["Motorista"].unique()]))
        filial_sel = st.selectbox("🏢 Filial:", ["Todas"] + sorted([str(x) for x in df_uni_base["Filial"].unique()]))
        cat_sel = st.selectbox("📦 Categoria:", ["Todas"] + sorted([str(x) for x in df_uni_base["Categoria"].unique()]))

    df_uni = df_uni_base.copy()
    df_danos = df_danos_base.copy()
    df_faltas = df_faltas_base.copy()
    df_trat1 = df_trat1_base.copy() if not df_trat1_base.empty else pd.DataFrame()
    df_trat2 = df_trat2_base.copy() if not df_trat2_base.empty else pd.DataFrame()

    if periodo_sel != "Todos":
        df_uni = df_uni[df_uni["Periodo"] == periodo_sel]
        df_danos = df_danos[df_danos["Periodo"] == periodo_sel]
        df_faltas = df_faltas[df_faltas["Periodo"] == periodo_sel]
    if motorista_sel != "Todos":
        df_uni = df_uni[df_uni["Motorista"] == motorista_sel]
        df_danos = df_danos[df_danos["Motorista"] == motorista_sel]
        df_faltas = df_faltas[df_faltas["Motorista"] == motorista_sel]
    if filial_sel != "Todas":
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
    if cat_sel != "Todas":
        df_uni = df_uni[df_uni["Categoria"] == cat_sel]
        df_danos = df_danos[df_danos["Categoria"] == cat_sel]
        df_faltas = df_faltas[df_faltas["Categoria"] == cat_sel]

    filial_map = df_uni.groupby('Motorista')['Filial'].agg(lambda x: x.mode()[0] if not x.empty else "N/A").to_dict() if not df_uni.empty else {}

    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9 = st.tabs([
        "🌐 Visão Integrada", "📦 Só Danos", "📉 Só Faltas", "🎯 Curva ABC",
        "🔄 Recorrência Motorista", "🛣️ Análise de Rotas", "📝 Tratativas",
        "🕵️ Recorrência Clientes", "🚨 Fraudes"    
    ])

    with aba1:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Ocorrências", len(df_uni))
        k2.metric("Apenas Danos", len(df_danos))
        k3.metric("Apenas Faltas", len(df_faltas))
        k4.metric("Itens Totais Afetados", int(df_uni["Quantidade"].sum()) if not df_uni.empty else 0)
        st.write("---")
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("**📊 Top 10 Motoristas (Volume de Itens)**")
            mapa_cores = {'Dano': '#1f77b4', 'Falta': '#d62728'}
            if not df_uni.empty:
                top_mot = df_uni.groupby('Motorista')['Quantidade'].sum().nlargest(10).index
                df_top = df_uni[df_uni['Motorista'].isin(top_mot)]
                cont_mot_tipo = df_top.groupby(['Motorista', 'Tipo_Ocorrencia'])['Quantidade'].sum().reset_index()
                cont_mot_tipo['Filial'] = cont_mot_tipo['Motorista'].map(filial_map)
                fig_bar = px.bar(cont_mot_tipo, x='Quantidade', y='Motorista', color='Tipo_Ocorrencia', barmode='stack', orientation='h', color_discrete_map=mapa_cores)
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
        with col_dir:
            st.markdown("**⚖️ Dano x Falta (Itens)**")
            if not df_uni.empty:
                cont_tipo = df_uni.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
                fig_pie = px.pie(cont_tipo, names='Tipo_Ocorrencia', values='Quantidade', hole=0.4, color_discrete_map=mapa_cores)
                st.plotly_chart(fig_pie, use_container_width=True)

    with aba2:
        st.markdown("### 🏢 Comparativo de Danos por Filial")
        if not df_danos.empty:
            cont_filial_d = df_danos.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
            fig_filial_d = px.bar(cont_filial_d, x='Filial', y='Quantidade', text='Quantidade', color='Quantidade', color_continuous_scale='Blues')
            fig_filial_d.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
            st.plotly_chart(fig_filial_d, use_container_width=True)
        st.write("---")
        st.markdown("### 📋 Tabela - Danos")
        st.dataframe(organizar_tabela(df_danos), use_container_width=True, height=250)

    with aba3:
        st.markdown("### 🏢 Comparativo de Faltas por Filial")
        if not df_faltas.empty:
            cont_filial_f = df_faltas.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
            fig_filial_f = px.bar(cont_filial_f, x='Filial', y='Quantidade', text='Quantidade', color='Quantidade', color_continuous_scale='Reds')
            fig_filial_f.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
            st.plotly_chart(fig_filial_f, use_container_width=True)
        st.write("---")
        st.markdown("### 📋 Tabela - Faltas")
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True, height=250)

    with aba4: st.info("🎯 Módulo em desenvolvimento.")
    with aba5: st.subheader("🔄 Análise de Recorrência")
    with aba6: st.subheader("🗺️ Mapeamento Geográfico")
    with aba7: st.subheader("📝 Controle de Tratativas")

    with aba8:
        st.subheader("🕵️ Recorrência de Clientes")
        if 'Cliente' in df_uni.columns:
            df_cli = df_uni[~df_uni['Cliente'].isin(['Não Identificado', 'NAN'])].dropna(subset=['Cliente'])
            if not df_cli.empty:
                rec_cli = df_cli.groupby('Cliente').agg(Ocorrencias=('Tipo_Ocorrencia', 'count'), Itens_Totais=('Quantidade', 'sum')).reset_index()
                rec_cli = rec_cli[rec_cli['Ocorrencias'] > 1].sort_values(by='Ocorrencias', ascending=False)
                st.metric("Clientes Reincidentes", len(rec_cli))
                st.dataframe(rec_cli, use_container_width=True, height=250)

    with aba9:
        st.subheader("🚨 Motor de Fraudes Natura")
        if 'Cliente' in df_uni.columns:
            df_fraude = df_uni[~df_uni['Cliente'].isin(['Não Identificado', 'NAN'])].copy()
            if not df_fraude.empty:
                f_vol = df_fraude[df_fraude['Quantidade'] >= 900].copy()
                f_vol['Motivo'] = 'Volume >900'

                df_rep = df_fraude[df_fraude['Quantidade'] >= 10].copy()
                cont_rep = df_rep.groupby(['Cliente', 'Quantidade']).size().reset_index(name='Vezes')
                cli_susp = cont_rep[cont_rep['Vezes'] > 1]
                f_rep = pd.merge(df_fraude, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'], how='inner')
                f_rep['Motivo'] = 'Reclamação Idêntica'

                df_alertas = pd.concat([f_vol, f_rep])
                if not df_alertas.empty:
                    df_alertas = df_alertas.drop_duplicates(subset=['Pedido', 'Cliente', 'Quantidade', 'Motivo'])
                    st.error(f"⚠️ {len(df_alertas)} Padrões Suspeitos!")
                    st.dataframe(df_alertas[['Motivo', 'Cliente', 'Pedido', 'Quantidade', 'Tipo_Ocorrencia', 'Motorista', 'Filial']], use_container_width=True)
                else:
                    st.success("✅ Nenhum indício de fraude detectado.")

except Exception as e:
    st.error(f"Erro no Dashboard: {e}")
    st.code(traceback.format_exc())
