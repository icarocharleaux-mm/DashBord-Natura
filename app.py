import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 🚀 AQUI ESTÁ A MÁGICA DA SEPARAÇÃO: Importando o nosso arquivo dados.py
from dados import load_data

# 1. Configuração da Página (DEVE sempre ser o primeiro comando do Streamlit)
st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")

# --- INJEÇÃO DE CSS RESPONSIVO ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        color: #2e4053; 
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        color: #555555;
    }
    
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.5rem; 
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem; 
        }
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            font-size: 1.8rem !important; 
        }
    }
</style>
""", unsafe_allow_html=True)

try:
    # 2. PUXANDO OS DADOS DO NOSSO OUTRO ARQUIVO
    df_danos_base, df_faltas_base, df_uni_base, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    st.title("🚀 Painel Integrado de Logística")
    st.markdown("Visão consolidada cruzando dados de **Danos**, **Faltas (NC)** e **Tratativas**.")
    
    # ==========================================
    # ALERTAS INTELIGENTES 
    # ==========================================
    if not df_uni_base.empty:
        total_ocorrencias = len(df_uni_base)
        pior_motorista = df_uni_base['Motorista'].value_counts().idxmax()
        qtd_pior_motorista = df_uni_base['Motorista'].value_counts().max()
        pct_motorista = (qtd_pior_motorista / total_ocorrencias) * 100
        pior_filial = df_uni_base['Filial'].value_counts().idxmax()
        pior_categoria = df_uni_base['Categoria'].value_counts().idxmax()
        
        alerta1, alerta2, alerta3 = st.columns(3)
        with alerta1:
            st.warning(f"⚠️ **Maior Ofensor:** {pior_motorista} ({pct_motorista:.1f}% do total).")
        with alerta2:
            st.error(f"🚨 **Filial Crítica:** {pior_filial} concentra o maior volume.")
        with alerta3:
            st.info(f"📦 **Categoria Sensível:** {pior_categoria} apresenta maior incidência.")
            
    st.divider()

    # ==========================================
    # # ==========================================
    # ÁREA DE FILTROS GLOBAIS
    # ==========================================
    with st.sidebar:
        # Adicionando a logo da empresa
        st.image("logodias.png", use_container_width=True)
        st.divider()
        st.header("🔍 Filtros Integrados")
        
        ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 
                       'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12, 'N/A': 99}
        meses_disponiveis = [m for m in df_uni_base["Periodo"].unique() if m != 'N/A']
        meses_disponiveis = sorted(meses_disponiveis, key=lambda x: ordem_meses.get(x, 100))
        opcoes_periodo = ["Todos"] + meses_disponiveis
        periodo_sel = st.selectbox("📅 Escolha o Mês:", opcoes_periodo)

        opcoes_motorista = ["Todos"] + sorted(df_uni_base["Motorista"].astype(str).unique().tolist())
        motorista_sel = st.selectbox("🚛 Motorista:", opcoes_motorista)

        opcoes_filial = ["Todas"] + sorted(df_uni_base["Filial"].astype(str).unique().tolist())
        filial_sel = st.selectbox("🏢 Filial:", opcoes_filial)

        opcoes_cat = ["Todas"] + sorted(df_uni_base["Categoria"].astype(str).unique().tolist())
        cat_sel = st.selectbox("📦 Categoria:", opcoes_cat)

    # APLICANDO OS FILTROS 
    df_uni = df_uni_base.copy()
    df_danos = df_danos_base.copy()
    df_faltas = df_faltas_base.copy()
    df_trat1 = df_trat1_base.copy()
    df_trat2 = df_trat2_base.copy()

    if periodo_sel != "Todos":
        df_uni = df_uni[df_uni["Periodo"] == periodo_sel]
        df_danos = df_danos[df_danos["Periodo"] == periodo_sel]
        df_faltas = df_faltas[df_faltas["Periodo"] == periodo_sel]

    if motorista_sel != "Todos":
        df_uni = df_uni[df_uni["Motorista"] == motorista_sel]
        df_danos = df_danos[df_danos["Motorista"] == motorista_sel]
        df_faltas = df_faltas[df_faltas["Motorista"] == motorista_sel]
        if not df_trat1.empty:
            df_trat1 = df_trat1[df_trat1["MOTORISTA"].astype(str).str.strip().str.upper() == str(motorista_sel).strip().upper()]
        if not df_trat2.empty:
            df_trat2 = df_trat2[df_trat2["MOTORISTA"].astype(str).str.strip().str.upper() == str(motorista_sel).strip().upper()]
        
    if filial_sel != "Todas":
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
        if not df_trat1.empty and 'FILIAL' in df_trat1.columns:
            df_trat1 = df_trat1[df_trat1["FILIAL"].astype(str).str.strip().str.upper() == str(filial_sel).strip().upper()]
        if not df_trat2.empty and 'FILIAL' in df_trat2.columns:
            df_trat2 = df_trat2[df_trat2["FILIAL"].astype(str).str.strip().str.upper() == str(filial_sel).strip().upper()]
        
    if cat_sel != "Todas":
        df_uni = df_uni[df_uni["Categoria"] == cat_sel]
        df_danos = df_danos[df_danos["Categoria"] == cat_sel]
        df_faltas = df_faltas[df_faltas["Categoria"] == cat_sel]

    # Dicionário de Filiais para Hover
    if not df_uni.empty:
        filial_map = df_uni.groupby('Motorista')['Filial'].agg(lambda x: x.mode()[0] if not x.empty else "N/A").to_dict()
    else:
        filial_map = {}

    # --- ABAS DE NAVEGAÇÃO ---
    aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
        "🌐 Visão Integrada", 
        "📦 Só Danos", 
        "📉 Só Faltas",
        "🎯 Curva ABC",
        "🔄 Recorrência",
        "🛣️ Análise de Rotas e Mapa",
        "📝 Planos & Tratativas"
    ])

    # ==========================================
    # ABA 1: CRUZAMENTO DE DADOS 
    # ==========================================
    with aba1:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total de Ocorrências", len(df_uni))
        k2.metric("Ocorrências de Dano", len(df_danos))
        k3.metric("Ocorrências de Falta", len(df_faltas))
        k4.metric("Itens Totais Afetados", int(df_uni["Quantidade"].sum()))
        st.write("---")
        
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("**📊 Motoristas x Tipo de Ocorrência**")
            contagem_mot_tipo = df_uni.groupby(['Motorista', 'Tipo_Ocorrencia']).size().reset_index(name='Ocorrências')
            top_motoristas = df_uni['Motorista'].value_counts().head(10).index
            contagem_mot_tipo = contagem_mot_tipo[contagem_mot_tipo['Motorista'].isin(top_motoristas)]
            
            mapa_cores = {'Dano': '#1f77b4', 'Falta': '#d62728'}
            if not contagem_mot_tipo.empty:
                contagem_mot_tipo['Filial'] = contagem_mot_tipo['Motorista'].map(filial_map)
                fig_bar = px.bar(contagem_mot_tipo, x='Ocorrências', y='Motorista', color='Tipo_Ocorrencia', 
                                 barmode='group', orientation='h', color_discrete_map=mapa_cores,
                                 hover_data={'Filial': True})
                fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        with col_dir:
            st.markdown("**⚖️ Proporção Dano x Falta**")
            contagem_tipo = df_uni['Tipo_Ocorrencia'].value_counts().reset_index()
            contagem_tipo.columns = ['Tipo', 'Quantidade']
            if not contagem_tipo.empty:
                fig_pie = px.pie(contagem_tipo, names='Tipo', values='Quantidade', hole=0.4, color='Tipo', color_discrete_map=mapa_cores)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)

    # ==========================================
    # ==========================================
    # ABA 2: DETALHES SOMENTE DANOS 
    # ==========================================
    with aba2:
        kd1, kd2, kd3, kd4 = st.columns(4)
        kd1.metric("Ocorrências de Dano", len(df_danos))
        kd2.metric("Motoristas Envolvidos", df_danos["Motorista"].nunique())
        kd3.metric("Filiais Afetadas", df_danos["Filial"].nunique())
        kd4.metric("Itens Reclamados", int(df_danos["Quantidade"].sum()))
        st.write("---")

        col_esq_d, col_dir_d = st.columns(2)
        with col_esq_d:
            st.markdown("**🚛 Top 10 Motoristas (Mais Danos)**")
            contagem_mot_danos = df_danos["Motorista"].value_counts().head(10).reset_index()
            contagem_mot_danos.columns = ['Motorista', 'Ocorrências'] 
            if not contagem_mot_danos.empty:
                contagem_mot_danos['Filial'] = contagem_mot_danos['Motorista'].map(filial_map)
                contagem_mot_danos['Classificação'] = ['Top 5 (Atenção)'] * min(5, len(contagem_mot_danos)) + ['Outros'] * max(0, len(contagem_mot_danos) - 5)
                mapa_cores_d = {'Top 5 (Atenção)': '#d62728', 'Outros': '#1f77b4'}
                fig_d1 = px.bar(contagem_mot_danos, x="Ocorrências", y="Motorista", orientation='h', color='Classificação', 
                                color_discrete_map=mapa_cores_d, hover_data={'Filial': True, 'Classificação': False}) 
                fig_d1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_d1, use_container_width=True)

        with col_dir_d:
            st.markdown("**📦 Danos por Categoria**")
            contagem_cat_danos = df_danos["Categoria"].value_counts().reset_index()
            contagem_cat_danos.columns = ['Categoria', 'Quantidade']
            if not contagem_cat_danos.empty:
                fig_d2 = px.pie(contagem_cat_danos, names="Categoria", values="Quantidade", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_d2.update_traces(textposition='inside', textinfo='percent+label')
                fig_d2.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_d2, use_container_width=True)

        st.write("---")
        st.dataframe(df_danos, use_container_width=True, height=250)

        # ✨ NOVO GRÁFICO: COMPARATIVO DE FILIAIS (DANOS) ✨
        st.write("---")
        st.markdown("### 🏢 Comparativo de Danos por Filial")
        if not df_danos.empty:
            contagem_filial_danos = df_danos["Filial"].value_counts().reset_index()
            contagem_filial_danos.columns = ['Filial', 'Ocorrências']
            
            fig_filial_d = px.bar(contagem_filial_danos, x='Filial', y='Ocorrências', 
                                  text='Ocorrências', color='Ocorrências', 
                                  color_continuous_scale='Blues')
            fig_filial_d.update_traces(textposition='outside', textfont_size=14)
            fig_filial_d.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, xaxis_title="Filial", yaxis_title="Nº de Danos")
            st.plotly_chart(fig_filial_d, use_container_width=True)

            # ==========================================
    # ABA 3: DETALHES SOMENTE FALTAS
    # ==========================================
    with aba3:
        kf1, kf2, kf3, kf4 = st.columns(4)
        kf1.metric("Ocorrências de Falta", len(df_faltas))
        kf2.metric("Motoristas Envolvidos", df_faltas["Motorista"].nunique())
        kf3.metric("Filiais Afetadas", df_faltas["Filial"].nunique())
        kf4.metric("Itens Faltantes", int(df_faltas["Quantidade"].sum()))
        st.write("---")

        col_esq_f, col_dir_f = st.columns(2)
        with col_esq_f:
            st.markdown("**🚛 Top 10 Motoristas (Mais Faltas)**")
            contagem_mot_faltas = df_faltas["Motorista"].value_counts().head(10).reset_index()
            contagem_mot_faltas.columns = ['Motorista', 'Ocorrências'] 
            if not contagem_mot_faltas.empty:
                contagem_mot_faltas['Filial'] = contagem_mot_faltas['Motorista'].map(filial_map)
                contagem_mot_faltas['Classificação'] = ['Top 5 (Atenção)'] * min(5, len(contagem_mot_faltas)) + ['Outros'] * max(0, len(contagem_mot_faltas) - 5)
                mapa_cores_f = {'Top 5 (Atenção)': '#d62728', 'Outros': '#7f7f7f'}
                fig_f1 = px.bar(contagem_mot_faltas, x="Ocorrências", y="Motorista", orientation='h', color='Classificação', 
                                color_discrete_map=mapa_cores_f, hover_data={'Filial': True, 'Classificação': False}) 
                fig_f1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_f1, use_container_width=True)

        with col_dir_f:
            st.markdown("**📦 Faltas por Categoria**")
            contagem_cat_faltas = df_faltas["Categoria"].value_counts().reset_index()
            contagem_cat_faltas.columns = ['Categoria', 'Quantidade']
            if not contagem_cat_faltas.empty:
                fig_f2 = px.pie(contagem_cat_faltas, names="Categoria", values="Quantidade", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_f2.update_traces(textposition='inside', textinfo='percent+label')
                fig_f2.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_f2, use_container_width=True)

        st.write("---")
        st.dataframe(df_faltas, use_container_width=True, height=250)

        # ✨ NOVO GRÁFICO: COMPARATIVO DE FILIAIS (FALTAS) ✨
        st.write("---")
        st.markdown("### 🏢 Comparativo de Faltas por Filial")
        if not df_faltas.empty:
            contagem_filial_faltas = df_faltas["Filial"].value_counts().reset_index()
            contagem_filial_faltas.columns = ['Filial', 'Ocorrências']
            
            fig_filial_f = px.bar(contagem_filial_faltas, x='Filial', y='Ocorrências', 
                                  text='Ocorrências', color='Ocorrências', 
                                  color_continuous_scale='Reds')
            fig_filial_f.update_traces(textposition='outside', textfont_size=14)
            fig_filial_f.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, xaxis_title="Filial", yaxis_title="Nº de Faltas")
            st.plotly_chart(fig_filial_f, use_container_width=True)

    # ==========================================
    # ABA 5: RECORRÊNCIA E HISTÓRICO
    # ==========================================
    with aba5:
        st.subheader("🔄 Análise de Recorrência Mensal")
        
        st.markdown("Filtre o histórico abaixo:")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            opcoes_mot_rec = sorted(df_uni_base["Motorista"].astype(str).unique().tolist())
            mot_sel_rec = st.multiselect("🚛 Filtrar Motoristas (vazio = todos):", opcoes_mot_rec)
            
        with col_f2:
            opcoes_filial_rec = sorted(df_uni_base["Filial"].astype(str).unique().tolist())
            filial_sel_rec = st.multiselect("🏢 Filtrar Filiais (vazio = todas):", opcoes_filial_rec)

        df_historico_filtrado = df_uni_base.copy()
        
        if len(mot_sel_rec) > 0:
            df_historico_filtrado = df_historico_filtrado[df_historico_filtrado["Motorista"].isin(mot_sel_rec)]
        if len(filial_sel_rec) > 0:
            df_historico_filtrado = df_historico_filtrado[df_historico_filtrado["Filial"].isin(filial_sel_rec)]
            
        df_historico = df_historico_filtrado.groupby(['Motorista', 'Periodo']).size().reset_index(name='Ocorrencias')
        df_historico = df_historico[df_historico['Periodo'] != 'N/A']
        
        meses_afetados = df_historico.groupby('Motorista')['Periodo'].nunique().reset_index(name='Qtd_Meses')
        motoristas_reincidentes = meses_afetados[meses_afetados['Qtd_Meses'] > 1]
        
        kr1, kr2, kr3 = st.columns(3)
        kr1.metric("Motoristas Reincidentes (> 1 mês)", len(motoristas_reincidentes))
        
        if not meses_afetados.empty:
            media_meses = meses_afetados['Qtd_Meses'].mean()
            max_meses = meses_afetados['Qtd_Meses'].max()
        else:
            media_meses, max_meses = 0, 0
            
        kr2.metric("Média de Meses c/ Ocorrência", f"{media_meses:.1f}")
        kr3.metric("Máximo de Meses c/ Ocorrência", int(max_meses))
        
        st.write("---")
        
        col_rec_esq, col_rec_dir = st.columns([2, 1])
        with col_rec_esq:
            st.markdown("**📅 Mapa de Calor: Evolução Mensal**")
            top_15_mot = df_historico_filtrado['Motorista'].value_counts().head(15).index
            df_heatmap = df_historico[df_historico['Motorista'].isin(top_15_mot)]
            
            df_pivot = df_heatmap.pivot_table(index='Motorista', columns='Periodo', values='Ocorrencias', aggfunc='sum', fill_value=0)
            
            meses_ordenados = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            colunas_presentes = [m for m in meses_ordenados if m in df_pivot.columns]
            df_pivot = df_pivot[colunas_presentes]
            
            if not df_pivot.empty:
                fig_heat = px.imshow(df_pivot, text_auto=True, aspect="auto", color_continuous_scale='Reds', labels=dict(x="Mês", y="Motorista", color="Ocorrências"))
                fig_heat.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Dados insuficientes.")
            
        with col_rec_dir:
            st.markdown("**📋 Tabela de Reincidentes**")
            df_tabela_rec = df_historico_filtrado[df_historico_filtrado['Periodo'] != 'N/A'].groupby('Motorista').agg(
                Total_Ocorrencias=('Tipo_Ocorrencia', 'count'),
                Meses_Distintos=('Periodo', 'nunique')
            ).reset_index()
            
            df_tabela_rec = df_tabela_rec[df_tabela_rec['Meses_Distintos'] > 1].sort_values(by=['Meses_Distintos', 'Total_Ocorrencias'], ascending=[False, False])
            
            if not df_tabela_rec.empty:
                st.dataframe(df_tabela_rec, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("Nenhum motorista reincidente encontrado.")

    # ==========================================
    # ABA 6: ANÁLISE DE ROTAS E MAPA
    # ==========================================
    with aba6:
        st.subheader("🗺️ Mapeamento Geográfico e Bolhas de Ocorrências")
        st.markdown("Veja as rotas com maior volume de problemas e navegue pelo mapa interativo de calor da sua operação.")
        
        df_rotas = df_uni[~df_uni['Rota'].str.upper().isin(['N/A', 'NÃO INFORMADA', 'NAN', ''])]
        
        if not df_rotas.empty:
            tabela_rotas = df_rotas.groupby('Rota').agg(
                Total_Danos=('Tipo_Ocorrencia', lambda x: (x == 'Dano').sum()),
                Total_Faltas=('Tipo_Ocorrencia', lambda x: (x == 'Falta').sum()),
                Total_Geral=('Tipo_Ocorrencia', 'count')
            ).reset_index()
            
            tabela_rotas['Rota'] = tabela_rotas['Rota'].astype(str)
            df_mapa_agg['Rota'] = df_mapa_agg['Rota'].astype(str)
            df_coord_agg['ROTA'] = df_coord_agg['ROTA'].astype(str)
            
            tabela_final_rotas = pd.merge(tabela_rotas, df_mapa_agg, on='Rota', how='left')
            tabela_final_rotas = pd.merge(tabela_final_rotas, df_coord_agg, left_on='Rota', right_on='ROTA', how='left')
            
            tabela_final_rotas['Setor'] = tabela_final_rotas['Setor'].fillna('Não Mapeado')
            tabela_final_rotas['Bairro'] = tabela_final_rotas['Bairro'].fillna('Sem informação')
            
            df_mapa_plot = tabela_final_rotas.dropna(subset=['LATITUDE', 'LONGITUDE'])
            
            if not df_mapa_plot.empty:
                fig_mapa = px.scatter_mapbox(
                    df_mapa_plot,
                    lat="LATITUDE",
                    lon="LONGITUDE",
                    size="Total_Geral",
                    color="Total_Geral",
                    color_continuous_scale=px.colors.sequential.Reds,
                    hover_name="Setor",
                    hover_data={
                        "Rota": True, "Bairro": True, "Total_Geral": True, 
                        "Total_Danos": True, "Total_Faltas": True,
                        "LATITUDE": False, "LONGITUDE": False
                    },
                    zoom=7, 
                    mapbox_style="carto-positron" 
                )
                fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.info("💡 A base 'base_coordenadas.csv' não foi carregada ou não contém pontos válidos.")
                
            st.write("---")

            kr1, kr2 = st.columns(2)
            rota_pior = df_rotas['Rota'].value_counts().idxmax()
            qtd_rota_pior = df_rotas['Rota'].value_counts().max()
            
            kr1.metric("Total de Rotas com Problemas", df_rotas['Rota'].nunique())
            kr2.metric("Rota Mais Crítica", str(rota_pior), f"{qtd_rota_pior} ocorrências globais", delta_color="inverse")
            
            tabela_exibicao = tabela_final_rotas[['Rota', 'Setor', 'Bairro', 'Total_Geral', 'Total_Danos', 'Total_Faltas']]
            tabela_exibicao.columns = ['ID da Rota', 'Região / Setor', 'Amostra de Bairros', 'Total Geral', 'Qtd Danos', 'Qtd Faltas']
            tabela_exibicao = tabela_exibicao.sort_values('Total Geral', ascending=False)
            
            st.dataframe(tabela_exibicao, use_container_width=True, hide_index=True, height=400)
            
            csv_rotas = tabela_exibicao.to_csv(index=False, sep=';').encode('latin-1')
            st.download_button(
                label="📥 Baixar Tabela Completa (Excel/CSV)",
                data=csv_rotas,
                file_name='rotas_bairros_cruzados.csv',
                mime='text/csv'
            )
            
        else:
            st.info("Não há dados de rotas disponíveis para os filtros selecionados.")

    # ==========================================
    # ABA 7: PLANOS DE AÇÃO E TRATATIVAS
    # ==========================================
    with aba7:
        st.subheader("📝 Controle de Tratativas e Planos de Ação")
        st.markdown("Acompanhamento das ações corretivas (justificativas) tomadas para cada filial e ofensor.")
        st.write("---")
        
        colunas_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'TOTAL', 'PERIODO', 'PERIDOD']

        if not df_trat1.empty:
            st.markdown("### 📋 Tratativas Faltas")
            col_limpas_1 = [c for c in df_trat1.columns if c not in colunas_meses]
            st.dataframe(df_trat1[col_limpas_1], use_container_width=True, hide_index=True, height=350)
            
            csv_trat1 = df_trat1.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Base 1 (Completa)",
                data=csv_trat1,
                file_name='Tratativas_Base1.csv',
                mime='text/csv'
            )

        st.write("---")

        if not df_trat2.empty:
            st.markdown("### 📋 Tratativas Danos")
            col_limpas_2 = [c for c in df_trat2.columns if c not in colunas_meses]
            st.dataframe(df_trat2[col_limpas_2], use_container_width=True, hide_index=True, height=350)
            
            csv_trat2 = df_trat2.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Base 2 (Completa)",
                data=csv_trat2,
                file_name='Tratativas_Base2.csv',
                mime='text/csv'
            )

except Exception as e:
    st.error(f"Erro ao processar o Dashboard Integrado: {e}")
