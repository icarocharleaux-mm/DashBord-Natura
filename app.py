import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importando o nosso arquivo dados.py
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
    
    colunas_iniciais = ['Cliente', 'Motorista', 'Filial', 'Pedido', 'Quantidade', 'Rota']
    colunas_iniciais = [c for c in colunas_iniciais if c in df.columns]
    
    colunas_esconder = ['transportadora', 'nome_transportadora', 'desvio_logistico', 'tipo_ocorrencia', 'mes_limpo', 'mes']
    outras_colunas = [c for c in df.columns if c not in colunas_iniciais and str(c).lower() not in colunas_esconder]
    return df[colunas_iniciais + outras_colunas]

try:
    # 2. PUXANDO OS DADOS
    df_danos_base, df_faltas_base, df_uni_base, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    st.title("🚀 Painel Integrado e Prevenção de Fraudes")
    st.markdown("Visão consolidada cruzando dados de **Danos**, **Faltas** e **Auditoria Logística**.")
    
    # ALERTAS INTELIGENTES 
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

    # FILTROS GLOBAIS
    with st.sidebar:
        st.header("🔍 Filtros Integrados")
        ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12, 'N/A': 99}
        meses_disponiveis = sorted([m for m in df_uni_base["Periodo"].unique() if m != 'N/A'], key=lambda x: ordem_meses.get(x, 100))
        periodo_sel = st.selectbox("📅 Escolha o Mês:", ["Todos"] + meses_disponiveis)
        motorista_sel = st.selectbox("🚛 Motorista:", ["Todos"] + sorted(df_uni_base["Motorista"].astype(str).unique().tolist()))
        filial_sel = st.selectbox("🏢 Filial:", ["Todas"] + sorted(df_uni_base["Filial"].astype(str).unique().tolist()))
        cat_sel = st.selectbox("📦 Categoria:", ["Todas"] + sorted(df_uni_base["Categoria"].astype(str).unique().tolist()))

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
    if filial_sel != "Todas":
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
    if cat_sel != "Todas":
        df_uni = df_uni[df_uni["Categoria"] == cat_sel]
        df_danos = df_danos[df_danos["Categoria"] == cat_sel]
        df_faltas = df_faltas[df_faltas["Categoria"] == cat_sel]

    filial_map = df_uni.groupby('Motorista')['Filial'].agg(lambda x: x.mode()[0] if not x.empty else "N/A").to_dict() if not df_uni.empty else {}

    # --- ABAS DE NAVEGAÇÃO ---
    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9 = st.tabs([
        "🌐 Visão Integrada", 
        "📦 Só Danos", 
        "📉 Só Faltas",
        "🎯 Curva ABC",
        "🔄 Recorrência Motorista",
        "🛣️ Análise de Rotas e Mapa",
        "📝 Planos & Tratativas",
        "🕵️ Recorrência Clientes", 
        "🚨 Indícios de Fraude"    
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
                fig_bar = px.bar(contagem_mot_tipo, x='Quantidade', y='Motorista', color='Tipo_Ocorrencia', barmode='stack', orientation='h', color_discrete_map=mapa_cores, hover_data={'Filial': True})
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
    # ABA 2 E 3: TABELAS
    # ==========================================
    with aba2:
        st.markdown("### 📋 Tabela Organizada - Danos")
        st.dataframe(organizar_tabela(df_danos), use_container_width=True, height=250)

    with aba3:
        st.markdown("### 📋 Tabela Organizada - Faltas")
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True, height=250)

    # ==========================================
    # ABAS 4 a 7: Módulos Originais
    # ==========================================
    with aba4: st.info("🎯 Módulo de Curva ABC em desenvolvimento.")
    with aba5: st.subheader("🔄 Análise de Recorrência Mensal (Motoristas)")
    with aba6: st.subheader("🗺️ Mapeamento Geográfico")
    with aba7: st.subheader("📝 Controle de Tratativas")

    # ==========================================
    # ABA 8: RECORRÊNCIA DE CLIENTES
    # ==========================================
    with aba8:
        st.subheader("🕵️ Investigação: Recorrência de Clientes")
        st.markdown("Identifique clientes com múltiplos acionamentos logísticos.")

        if 'Cliente' in df_uni.columns:
            df_clientes = df_uni[df_uni['Cliente'].astype(str).str.strip().str.upper() != 'NÃO IDENTIFICADO'].dropna(subset=['Cliente'])
            if not df_clientes.empty:
                rec_clientes = df_clientes.groupby('Cliente').agg(
                    Ocorrencias=('Tipo_Ocorrencia', 'count'),
                    Itens_Totais=('Quantidade', 'sum'),
                    Tipos=('Tipo_Ocorrencia', lambda x: ', '.join(x.unique())),
                    Motoristas=('Motorista', lambda x: ', '.join(x.unique()))
                ).reset_index()

                rec_clientes = rec_clientes[rec_clientes['Ocorrencias'] > 1].sort_values(by='Ocorrencias', ascending=False)
                st.metric("Total de Clientes Reincidentes (> 1 Ocorrência)", len(rec_clientes))
                
                col_c1, col_c2 = st.columns([1, 2])
                with col_c1:
                    st.markdown("**🏆 Top 10 Clientes (Por Ocorrências)**")
                    fig_cli = px.bar(rec_clientes.head(10), x='Ocorrencias', y='Cliente', orientation='h', text='Itens_Totais')
                    fig_cli.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_cli, use_container_width=True)
                with col_c2:
                    st.markdown("**📋 Tabela Completa de Clientes Reincidentes**")
                    st.dataframe(rec_clientes, use_container_width=True, height=350)
            else:
                st.info("Nenhum cliente identificado com as regras atuais.")

    # ==========================================
    # 🚨 ABA 9: MOTOR DE PREVENÇÃO A FRAUDES 🚨
    # ==========================================
    with aba9:
        st.subheader("🚨 Prevenção a Fraudes Natura")
        st.markdown("Auditoria automática buscando volumes críticos e padrões suspeitos de fracionamento de reclamações.")

        if 'Cliente' in df_uni.columns:
            df_fraude_base = df_uni[df_uni['Cliente'].astype(str).str.strip().str.upper() != 'NÃO IDENTIFICADO'].dropna(subset=['Cliente']).copy()
            
            if not df_fraude_base.empty:
                # REGRA 1: Volume Absurdo (> 900 itens)
                fraude_volume = df_fraude_base[df_fraude_base['Quantidade'] >= 900].copy()
                fraude_volume['Motivo_Suspeita'] = 'Volume Crítico (>900 itens)'

                # REGRA 2: Reclamações repetidas idênticas (>10 itens)
                df_repetidos = df_fraude_base[df_fraude_base['Quantidade'] >= 10].copy()
                contagem_rep = df_repetidos.groupby(['Cliente', 'Quantidade']).size().reset_index(name='Vezes_Repetido')
                clientes_suspeitos = contagem_rep[contagem_rep['Vezes_Repetido'] > 1]
                
                fraude_repetida = pd.merge(df_fraude_base, clientes_suspeitos[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'], how='inner')
                fraude_repetida['Motivo_Suspeita'] = 'Reclamação Idêntica Repetida'

                # Junta as fraudes
                df_alertas = pd.concat([fraude_volume, fraude_repetida])
                
                # ✨ AQUI ESTÁ A TRAVA DE SEGURANÇA QUE PREVINE O ERRO INDEX
                if not df_alertas.empty:
                    colunas_subset = [c for c in ['Pedido', 'Cliente', 'Quantidade', 'Motivo_Suspeita'] if c in df_alertas.columns]
                    df_alertas = df_alertas.drop_duplicates(subset=colunas_subset)
                    
                    st.error(f"⚠️ ATENÇÃO: Encontrados {len(df_alertas)} registros com padrões suspeitos para auditoria Natura.")
                    
                    colunas_exibir = ['Motivo_Suspeita', 'Cliente', 'Pedido', 'Quantidade', 'Tipo_Ocorrencia', 'Motorista', 'Filial', 'Periodo']
                    colunas_exibir = [c for c in colunas_exibir if c in df_alertas.columns]
                    
                    st.dataframe(df_alertas[colunas_exibir], use_container_width=True, height=400)
                    
                    csv_fraudes = df_alertas[colunas_exibir].to_csv(index=False, sep=';').encode('latin-1')
                    st.download_button(
                        label="📥 Baixar Dossiê de Fraudes (Envio Natura)",
                        data=csv_fraudes,
                        file_name="Alerta_Fraudes_Natura.csv",
                        mime="text/csv",
                        type="primary"
                    )
                else:
                    st.success("✅ O motor rodou perfeitamente. Nenhum indício de fraude detectado com os filtros atuais.")
        else:
            st.warning("⚠️ Atualize o arquivo 'dados.py' incluindo a coluna 'Cliente' nas 'colunas_comuns'.")

except Exception as e:
    st.error(f"Erro ao processar o Dashboard Integrado: {e}")