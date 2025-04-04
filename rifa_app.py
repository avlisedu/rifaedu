import streamlit as st
import psycopg2
import os
from supabase import create_client

# ======== CONEXÃO COM BANCO POSTGRES (SUPABASE) ========
def conectar():
    return psycopg2.connect(
        host="db.xkwusqpqmtjfehabofiv.supabase.co",
        database="postgres",
        user="postgres",
        password=st.secrets["DB_PASSWORD"],
        port="5432"
    )

# ======== CONEXÃO COM STORAGE SUPABASE ========
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======== BANCO: CRIAR TABELA SE NÃO EXISTIR ========
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rifa (
            id serial PRIMARY KEY,
            numero integer NOT NULL,
            nome text NOT NULL,
            contato text,
            comprovante text,
            data_reserva timestamp DEFAULT current_timestamp
        )
    ''')
    conn.commit()
    conn.close()

# ======== BANCO: CONSULTAR NÚMEROS RESERVADOS ========
def numeros_reservados():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT numero FROM rifa")
    reservados = [row[0] for row in cursor.fetchall()]
    conn.close()
    return reservados

# ======== BANCO: SALVAR NOVA RESERVA ========
def reservar_numero(numero, nome, contato, comprovante_path):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rifa (numero, nome, contato, comprovante) VALUES (%s, %s, %s, %s)",
                   (numero, nome, contato, comprovante_path))
    conn.commit()
    conn.close()

# ======== INÍCIO DO APP STREAMLIT ========
inicializar_banco()

if "limite_numeros" not in st.session_state:
    st.session_state["limite_numeros"] = 100

st.title("🎟️ Rifa Solidária - Prêmio R$200")
st.markdown("Escolha um número disponível e preencha seus dados para participar.")
st.markdown("🔢 Começamos com 100 números, mas você pode carregar mais se quiser!")

reservados = numeros_reservados()
colunas = st.columns(10)

for i in range(1, st.session_state["limite_numeros"] + 1):
    col = colunas[(i - 1) % 10]
    if i in reservados:
        col.button(f"{i}", disabled=True)
    else:
        if col.button(f"{i}", key=f"botao_{i}"):
            st.session_state["numero_selecionado"] = i

if st.button("🔁 Ver mais números"):
    st.session_state["limite_numeros"] += 50

# ======== FORMULÁRIO DE RESERVA ========
if "numero_selecionado" in st.session_state:
    numero_selecionado = st.session_state["numero_selecionado"]
    st.success(f"Você escolheu o número **{numero_selecionado}**! Preencha seus dados para confirmar:")

    nome = st.text_input("Nome completo")
    contato = st.text_input("WhatsApp ou Instagram")
    comprovante = st.file_uploader("Comprovante de pagamento (opcional)", type=["png", "jpg", "jpeg", "pdf"])

    if st.button("✅ Confirmar reserva"):
        if numero_selecionado in numeros_reservados():
            st.error("Esse número acabou de ser reservado por outra pessoa 😢")
        elif not nome.strip():
            st.error("Por favor, preencha seu nome.")
        elif not contato.strip():
            st.error("Informe seu WhatsApp ou Instagram para contato.")
        else:
            caminho = ""
            if comprovante:
                nome_arquivo = f"{numero_selecionado}_{comprovante.name}"
                conteudo = comprovante.getvalue()

                # Upload para bucket privado
                supabase.storage.from_("comprovantes").upload(
                    path=nome_arquivo,
                    file=conteudo,
                    file_options={"content-type": comprovante.type}
                )
                caminho = nome_arquivo

            reservar_numero(numero_selecionado, nome.strip(), contato.strip(), caminho)
            st.success(f"Número {numero_selecionado} reservado com sucesso! ✅")
            st.balloons()
            del st.session_state["numero_selecionado"]
            st.rerun()

# ======== VISUALIZAÇÃO DE RESERVAS (OPCIONAL) ========
if st.checkbox("📋 Ver reservas registradas"):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT numero, nome, contato, comprovante, data_reserva FROM rifa ORDER BY numero")
    reservas = cursor.fetchall()
    conn.close()

    for numero, nome, contato, arquivo, data in reservas:
        st.markdown(f"🔢 **{numero}** | {nome} ({contato}) – {data.strftime('%d/%m/%Y %H:%M')}")
        if arquivo:
            signed_url = supabase.storage.from_("comprovantes").create_signed_url(arquivo, 60)
            st.markdown(f"[📎 Ver comprovante (válido por 1 min)]({signed_url['signedURL']})")
        st.markdown("---")
