import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback

from dados import load_data

# 1. Configuração da Página
st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")

# --- INJEÇÃO DE CSS RESPONSIVO ---
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

# --- FUNÇÃO PARA ORGANIZAR AS TABELAS ---
def organizar_tabela(df_entrada):
    if df_entrada.empty:
        return df_entrada
        
    df = df_entrada.copy()
    if 'nm_pedido' in df.columns:
        df = df.rename(columns={'nm_pedido': 'Pedido'})
        
    colunas_iniciais = ['Cliente', 'Empresa', 'Canal', 'Motorista', 'Filial', 'Pedido', 'Quantidade', 'Rota']
    colunas_iniciais = [c for c in colunas_iniciais if c in df.columns]
    colunas_esconder = ['transportadora', 'nome_transportadora', 'desvio_logistico', 'tipo_ocorrencia', 'mes_limpo', 'mes']
    outras_colunas = [c for c in df.columns if c not in colunas_iniciais and str(c).lower() not in colunas_esconder]
    
    ordem_final = colunas_iniciais + outras_colunas
    return df[ordem_final]

try:
    # 2. PUXANDO OS DADOS DO NOSSO OUTRO ARQUIVO
    df_danos_base, df_faltas_base, df_uni_base, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    # ==========================================
    # 🛡️ A VACINA BLINDADA (Colunas Faltantes e Tipos)
    # ==========================================
    colunas_vitais = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Tipo_Ocorrencia', 'Pedido', 'Rota', 'Quantidade', 'Empresa', 'Canal']
    
    for df_limpo in [df_danos_base, df_faltas_base, df_uni_base]:
        if not df_limpo.empty:
            for col in colunas_vitais:
                if col not in df_limpo.columns:
                    df_limpo[col] = 'Não Identificado' if col != 'Quantidade' else 0
                    
            df_limpo['Quantidade'] = pd.to_numeric(df_limpo['Quantidade'], errors='coerce').fillna(0)
            
            colunas_texto = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Tipo_Ocorrencia', 'Pedido', 'Rota', 'Empresa', 'Canal']
            for col in colunas_texto:
                df_limpo[col] = df_limpo[col].astype(str).str.strip()
                df_limpo.loc[df_limpo[col].str.lower() == 'nan', col] = 'Não Identificado'

    st.title("🚀 Painel Integrado de Logística")
    st.markdown("Visão consolidada cruzando dados de **Danos**, **Faltas (NC)** e **Tratativas**.")
    st.divider()

    # ==========================================
    # ÁREA DE FILTROS GLOBAIS
    # ==========================================
    with st.sidebar:
        st.header("🔍 Filtros Integrados")
        
        ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 
                       'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12, 'N/A': 99, 'Não Identificado': 99}
        meses_disponiveis = [m for m in df_uni_base["Periodo"].unique() if m not in ['N/A', 'Não Identificado']]
        meses_disponiveis = sorted(meses_disponiveis, key=lambda x: ordem_meses.get(x, 100))
        
        periodo_sel = st.selectbox("📅 Escolha o Mês:", ["Todos"] + meses_disponiveis)
        filial_sel = st.selectbox("🏢 Filial:", ["Todas"] + sorted(df_uni_base["Filial"].unique().tolist()))
        motorista_sel = st.selectbox("🚛 Motorista:", ["Todos"] + sorted(df_uni_base["Motorista"].unique().tolist()))
        
        opcoes_empresa = [str(x) for x in df_uni_base["Empresa"].unique() if str(x) not in ['Não Identificado', 'N/A', 'nan']]
        empresa_sel = st.selectbox("🏭 Empresa (Danos):", ["Todas"] + sorted(opcoes_empresa))
        
        opcoes_canal = [str(x) for x in df_uni_base["Canal"].unique() if str(x) not in ['Não Identificado', 'N/A', 'nan']]
        canal_sel = st.multiselect("🛍️ Marca Canal (Faltas) [Vazio = Todos]:", sorted(opcoes_canal))


    # APLICANDO OS FILTROS 
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
        if not df_trat1.empty and 'MOTORISTA' in df_trat1.columns:
            df_trat1 = df_trat1[df_trat1["MOTORISTA"].astype(str).str.strip().str.upper() == str(motorista_sel).strip().upper()]
        if not df_trat2.empty and 'MOTORISTA' in df_trat2.columns:
            df_trat2 = df_trat2[df_trat2["MOTORISTA"].astype(str).str.strip().str.upper() == str(motorista_sel).strip().upper()]
        
    if filial_sel != "Todas":
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
        if not df_trat1.empty and 'FILIAL' in df_trat1.columns:
            df_trat1 = df_trat1[df_trat1["FILIAL"].astype(str).str.strip().str.upper() == str(filial_sel).strip().upper()]
        if not df_trat2.empty and 'FILIAL' in df_trat2.columns:
            df_trat2 = df_trat2[df_trat2["FILIAL"].astype(str).str.strip().str.upper() == str(filial_sel).strip().upper()]
            
    if empresa_sel != "Todas":
        df_uni = df_uni[df_uni["Empresa"] == empresa_sel]
        df_danos = df_danos[df_danos["Empresa"] == empresa_sel]
        df_faltas = df_faltas[df_faltas["Empresa"] == empresa_sel]
        
    if len(canal_sel) > 0:
        df_uni = df_uni[df_uni["Canal"].isin(canal_sel)]
        df_danos = df_danos[df_danos["Canal"].isin(canal_sel)]
        df_faltas = df_faltas[df_faltas["Canal"].isin(canal_sel)]

    if not df_uni.empty:
        filial_map = df_uni.groupby('Motorista')['Filial'].agg(lambda x: x.mode()[0] if not x.empty else "N/A").to_dict()
    else:
        filial_map = {}

    # --- ABAS DE NAVEGAÇÃO ---
    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8 = st.tabs([
        "🌐 Visão Integrada", 
        "📦 Só Danos", 
        "📉 Só Faltas",
        "🎯 Curva ABC",
        "🔄 Recorrência",
        "🛣️ Análise de Rotas e Mapa",
        "📝 Tratativas",
        "🚨 Dossiê de Fraudes"
    ])

    # ==========================================
    # ABA 1: CRUZAMENTO DE DADOS 
    # ==========================================
    with aba1:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total de Ocorrências (Linhas)", len(df_uni))
        k2.metric("Ocorrências de Dano", len(df_danos))
        k3.metric("Ocorrências de Falta", len(df_faltas))
        k4.metric("Itens Totais Afetados", int(df_uni["Quantidade"].sum()) if not df_uni.empty else 0)
        st.write("---")
        
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("**📊 Top 10 Motoristas x Tipo de Ocorrência (Volume de Itens)**")
            mapa_cores = {'Dano': '#1f77b4', 'Falta': '#d62728'}
            if not df_uni.empty:
                top_motoristas = df_uni.groupby('Motorista')['Quantidade'].sum().nlargest(10).index
                df_top = df_uni[df_uni['Motorista'].isin(top_motoristas)]
                contagem_mot_tipo = df_top.groupby(['Motorista', 'Tipo_Ocorrencia'])['Quantidade'].sum().reset_index()
                
                contagem_mot_tipo['Filial'] = contagem_mot_tipo['Motorista'].map(filial_map)
                fig_bar = px.bar(contagem_mot_tipo, x='Quantidade', y='Motorista', color='Tipo_Ocorrencia', 
                                 barmode='stack', orientation='h', color_discrete_map=mapa_cores,
                                 hover_data={'Filial': True})
                fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        with col_dir:
            st.markdown("**⚖️ Proporção Dano x Falta (Por Itens)**")
            if not df_uni.empty:
                contagem_tipo = df_uni.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
                fig_pie = px.pie(contagem_tipo, names='Tipo_Ocorrencia', values='Quantidade', hole=0.4, color='Tipo_Ocorrencia', color_discrete_map=mapa_cores)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)

    # ==========================================
    # ABA 2: DETALHES SOMENTE DANOS 
    # ==========================================
    with aba2:
        kd1, kd2, kd3, kd4 = st.columns(4)
        kd1.metric("Ocorrências de Dano (Linhas)", len(df_danos))
        kd2.metric("Motoristas Envolvidos", df_danos["Motorista"].nunique())
        kd3.metric("Filiais Afetadas", df_danos["Filial"].nunique())
        kd4.metric("Itens Reclamados", int(df_danos["Quantidade"].sum()) if not df_danos.empty else 0)
        st.write("---")

        col_esq_d, col_dir_d = st.columns(2)
        with col_esq_d:
            st.markdown("**🚛 Top 10 Motoristas (Mais Itens Danificados)**")
            if not df_danos.empty:
                contagem_mot_danos = df_danos.groupby("Motorista")["Quantidade"].sum().reset_index().sort_values(by="Quantidade", ascending=False).head(10)
                contagem_mot_danos['Filial'] = contagem_mot_danos['Motorista'].map(filial_map)
                contagem_mot_danos['Classificação'] = ['Top 5 (Atenção)'] * min(5, len(contagem_mot_danos)) + ['Outros'] * max(0, len(contagem_mot_danos) - 5)
                mapa_cores_d = {'Top 5 (Atenção)': '#d62728', 'Outros': '#1f77b4'}
                fig_d1 = px.bar(contagem_mot_danos, x="Quantidade", y="Motorista", orientation='h', color='Classificação', 
                                color_discrete_map=mapa_cores_d, hover_data={'Filial': True, 'Classificação': False}) 
                fig_d1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="Total de Itens", yaxis_title="", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_d1, use_container_width=True)

        with col_dir_d:
            st.markdown("**🏢 Comparativo de Danos por Filial (Itens)**")
            if not df_danos.empty:
                contagem_filial_danos = df_danos.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
                fig_filial_d = px.bar(contagem_filial_danos, x='Filial', y='Quantidade', 
                                      text='Quantidade', color='Quantidade', color_continuous_scale='Blues')
                fig_filial_d.update_traces(textposition='outside', textfont_size=14)
                fig_filial_d.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, 
                                           xaxis_title="Filial", yaxis_title="Total de Itens", xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_filial_d, use_container_width=True)

        st.write("---")
        st.markdown("### 📋 Tabela Organizada - Danos")
        st.dataframe(organizar_tabela(df_danos), use_container_width=True, height=250)

    # ==========================================
    # ABA 3: DETALHES SOMENTE FALTAS
    # ==========================================
    with aba3:
        kf1, kf2, kf3, kf4 = st.columns(4)
        kf1.metric("Ocorrências de Falta (Linhas)", len(df_faltas))
        kf2.metric("Motoristas Envolvidos", df_faltas["Motorista"].nunique())
        kf3.metric("Filiais Afetadas", df_faltas["Filial"].nunique())
        kf4.metric("Itens Faltantes", int(df_faltas["Quantidade"].sum()) if not df_faltas.empty else 0)
        st.write("---")

        col_esq_f, col_dir_f = st.columns(2)
        with col_esq_f:
            st.markdown("**🚛 Top 10 Motoristas (Mais Itens Faltantes)**")
            if not df_faltas.empty:
                contagem_mot_faltas = df_faltas.groupby("Motorista")["Quantidade"].sum().reset_index().sort_values(by="Quantidade", ascending=False).head(10)
                contagem_mot_faltas['Filial'] = contagem_mot_faltas['Motorista'].map(filial_map)
                contagem_mot_faltas['Classificação'] = ['Top 5 (Atenção)'] * min(5, len(contagem_mot_faltas)) + ['Outros'] * max(0, len(contagem_mot_faltas) - 5)
                mapa_cores_f = {'Top 5 (Atenção)': '#d62728', 'Outros': '#7f7f7f'}
                fig_f1 = px.bar(contagem_mot_faltas, x="Quantidade", y="Motorista", orientation='h', color='Classificação', 
                                color_discrete_map=mapa_cores_f, hover_data={'Filial': True, 'Classificação': False}) 
                fig_f1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="Total de Itens", yaxis_title="", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_f1, use_container_width=True)

        with col_dir_f:
            st.markdown("**🏢 Comparativo de Faltas por Filial (Itens)**")
            if not df_faltas.empty:
                contagem_filial_faltas = df_faltas.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
                fig_filial_f = px.bar(contagem_filial_faltas, x='Filial', y='Quantidade', 
                                      text='Quantidade', color='Quantidade', color_continuous_scale='Reds')
                fig_filial_f.update_traces(textposition='outside', textfont_size=14)
                fig_filial_f.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, 
                                           xaxis_title="Filial", yaxis_title="Total de Itens", xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_filial_f, use_container_width=True)

        st.write("---")
        st.markdown("### 📋 Tabela Organizada - Faltas")
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True, height=250)

    # ==========================================
    # ABA 4: CURVA ABC
    # ==========================================
    with aba4:
        st.subheader("🎯 Classificação ABC por Motorista (Volume de Itens)")
        if not df_uni_base.empty:
            abc_data = df_uni_base.groupby('Motorista')['Quantidade'].sum().sort_values(ascending=False).reset_index()
            abc_data['SomaAcumulada'] = abc_data['Quantidade'].cumsum()
            abc_data['PercentagemAcumulada'] = 100 * abc_data['SomaAcumulada'] / abc_data['Quantidade'].sum()
            
            def classificar_abc(p):
                if p <= 70: return 'A (Crítico - 70%)'
                elif p <= 90: return 'B (Atenção - 20%)'
                else: return 'C (Normal - 10%)'
                
            abc_data['Classe_ABC'] = abc_data['PercentagemAcumulada'].apply(classificar_abc)
            
            fig_abc = px.bar(abc_data, x='Motorista', y='Quantidade', color='Classe_ABC', 
                             title="Curva ABC de Ofensores",
                             color_discrete_map={'A (Crítico - 70%)': '#d62728', 'B (Atenção - 20%)': '#ff7f0e', 'C (Normal - 10%)': '#2ca02c'})
            st.plotly_chart(fig_abc, use_container_width=True)
            st.dataframe(abc_data, use_container_width=True)
        else:
            st.info("Aguardando dados para calcular a Curva ABC.")

    # ==========================================
    # ABA 5: RECORRÊNCIA MENSAL
    # ==========================================
    with aba5:
        st.subheader("🔄 Histórico Mensal de Ofensores")
        if not df_uni_base.empty:
            df_hist = df_uni_base.groupby(['Motorista', 'Periodo']).size().reset_index(name='Casos')
            df_pivot = df_hist.pivot_table(index='Motorista', columns='Periodo', values='Casos', fill_value=0)
            
            fig_heat = px.imshow(df_pivot.head(25), text_auto=True, color_continuous_scale='YlOrRd', title="Intensidade de Ocorrências (Top 25 Motoristas)")
            st.plotly_chart(fig_heat, use_container_width=True)
            
            recorrencia = df_uni_base.groupby('Motorista')['Periodo'].nunique().sort_values(ascending=False).reset_index()
            recorrencia.columns = ['Motorista', 'Qtd_Meses_Diferentes']
            st.markdown("**Motoristas com alta recorrência no longo prazo:**")
            st.dataframe(recorrencia[recorrencia['Qtd_Meses_Diferentes'] > 1], use_container_width=True)
        else:
            st.info("Aguardando dados.")

    # ==========================================
    # ABA 6: MAPA DE ROTAS
    # ==========================================
    with aba6:
        st.subheader("🗺️ Mapeamento Geográfico e Bolhas de Ocorrências")
        df_rotas = df_uni[~df_uni['Rota'].str.upper().isin(['N/A', 'NÃO INFORMADA', 'NAN', 'NÃO IDENTIFICADO', ''])]
        
        if not df_rotas.empty:
            tabela_rotas = df_rotas.groupby('Rota').agg(
                Total_Danos=('Tipo_Ocorrencia', lambda x: (x == 'Dano').sum()),
                Total_Faltas=('Tipo_Ocorrencia', lambda x: (x == 'Falta').sum()),
                Total_Geral=('Tipo_Ocorrencia', 'count')
            ).reset_index()
            
            # ✨ A CORREÇÃO DA ROTA: Agora as três tabelas se enxergam perfeitamente
            tabela_rotas['Rota'] = tabela_rotas['Rota'].astype(str)
            
            if not df_mapa_agg.empty and 'Rota' in df_mapa_agg.columns: 
                df_mapa_agg['Rota'] = df_mapa_agg['Rota'].astype(str)
            else: 
                df_mapa_agg = pd.DataFrame(columns=['Rota', 'Setor', 'Bairro'])
                
            if not df_coord_agg.empty and 'Rota' in df_coord_agg.columns: 
                df_coord_agg['Rota'] = df_coord_agg['Rota'].astype(str)
            else: 
                df_coord_agg = pd.DataFrame(columns=['Rota', 'LATITUDE', 'LONGITUDE'])
            
            tabela_final_rotas = pd.merge(tabela_rotas, df_mapa_agg, on='Rota', how='left')
            tabela_final_rotas = pd.merge(tabela_final_rotas, df_coord_agg, on='Rota', how='left')
            
            tabela_final_rotas['Setor'] = tabela_final_rotas['Setor'].fillna('Não Mapeado')
            tabela_final_rotas['Bairro'] = tabela_final_rotas['Bairro'].fillna('Sem informação')
            
            df_mapa_plot = tabela_final_rotas.dropna(subset=['LATITUDE', 'LONGITUDE'])
            if not df_mapa_plot.empty:
                fig_mapa = px.scatter_mapbox(
                    df_mapa_plot, lat="LATITUDE", lon="LONGITUDE", size="Total_Geral", color="Total_Geral",
                    color_continuous_scale=px.colors.sequential.Reds, hover_name="Setor",
                    hover_data={"Rota": True, "Bairro": True, "Total_Geral": True, "Total_Danos": True, "Total_Faltas": True, "LATITUDE": False, "LONGITUDE": False},
                    zoom=7, mapbox_style="carto-positron"
                )
                fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else: 
                st.info("💡 As rotas filtradas atualmente não possuem coordenadas mapeadas no arquivo 'base_coordenadas.csv'.")
                
            st.write("---")
            tabela_exibicao = tabela_final_rotas[['Rota', 'Setor', 'Bairro', 'Total_Geral', 'Total_Danos', 'Total_Faltas']].sort_values('Total_Geral', ascending=False)
            st.dataframe(tabela_exibicao, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("Não há dados de rotas disponíveis para os filtros selecionados.")

    # ==========================================
    # ABA 7: TRATATIVAS
    # ==========================================
    with aba7:
        st.subheader("📝 Controle de Tratativas")
        colunas_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'TOTAL', 'PERIODO', 'PERIDOD']
        if not df_trat1.empty:
            st.markdown("### Tratativas Faltas")
            col_limpas_1 = [c for c in df_trat1.columns if c not in colunas_meses]
            st.dataframe(df_trat1[col_limpas_1], use_container_width=True, hide_index=True, height=250)
        if not df_trat2.empty:
            st.markdown("### Tratativas Danos")
            col_limpas_2 = [c for c in df_trat2.columns if c not in colunas_meses]
            st.dataframe(df_trat2[col_limpas_2], use_container_width=True, hide_index=True, height=250)

    # ==========================================
    # ABA 8: FRAUDES E CLIENTES
    # ==========================================
    with aba8:
        st.subheader("🚨 Dossiê de Fraudes e Recorrência de Clientes")
        
        if 'Cliente' in df_uni.columns:
            df_cli = df_uni[~df_uni['Cliente'].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
            if not df_cli.empty:
                
                # 1. Recorrência Geral do Cliente
                st.markdown("#### 🕵️ Clientes com Múltiplos Acionamentos (Visão Geral)")
                rec_cli = df_cli.groupby('Cliente').agg(Ocorrencias=('Tipo_Ocorrencia', 'count'), Itens_Totais=('Quantidade', 'sum')).reset_index()
                rec_cli = rec_cli[rec_cli['Ocorrencias'] > 1].sort_values(by='Ocorrencias', ascending=False)
                st.dataframe(rec_cli.head(20), use_container_width=True, height=250)
                
                st.write("---")
                
                # 2. MOTOR DE FRAUDES
                st.markdown("#### 🔍 Auditoria Automática (Padrões Suspeitos)")
                f_vol = df_cli[df_cli['Quantidade'] >= 900].copy()
                f_vol['Motivo_Suspeita'] = 'Volume Crítico (>900 itens)'

                df_rep = df_cli[df_cli['Quantidade'] >= 10].copy()
                cont_rep = df_rep.groupby(['Cliente', 'Quantidade']).size().reset_index(name='Vezes_Repetido')
                cli_susp = cont_rep[cont_rep['Vezes_Repetido'] > 1]
                
                f_rep = pd.merge(df_cli, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'], how='inner')
                f_rep['Motivo_Suspeita'] = 'Reclamação Idêntica Repetida'

                df_alertas = pd.concat([f_vol, f_rep])
                
                if not df_alertas.empty:
                    df_alertas = df_alertas.drop_duplicates(subset=['Pedido', 'Cliente', 'Quantidade', 'Motivo_Suspeita'])
                    st.error(f"⚠️ ATENÇÃO: {len(df_alertas)} registros com padrões suspeitos.")
                    colunas_exibir = ['Motivo_Suspeita', 'Cliente', 'Pedido', 'Quantidade', 'Tipo_Ocorrencia', 'Motorista', 'Filial', 'Empresa', 'Canal', 'Periodo']
                    colunas_exibir = [c for c in colunas_exibir if c in df_alertas.columns]
                    st.dataframe(df_alertas[colunas_exibir], use_container_width=True, height=400)
                    
                    csv_fraudes = df_alertas[colunas_exibir].to_csv(index=False, sep=';').encode('latin-1')
                    st.download_button("📥 Baixar Dossiê de Fraudes", data=csv_fraudes, file_name="Alerta_Fraudes.csv", mime="text/csv", type="primary")
                else:
                    st.success("✅ Nenhum indício de fraude detectado com os filtros atuais.")
            else:
                st.info("Sem dados de clientes para analisar.")

except Exception as e:
    st.error(f"Erro ao processar o Dashboard Integrado: {e}")
    st.code(traceback.format_exc())