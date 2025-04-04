import streamlit as st
import psycopg2
import os

# ======== CONEXÃO COM O SUPABASE ========

def conectar():
    return psycopg2.connect(
        host="db.xkwusqpqmtjfehabofiv.supabase.co",
        database="postgres",
        user="postgres",
        password="@Percata23",
        port="5432"
    )

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

def numeros_reservados():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT numero FROM rifa")
    reservados = [row[0] for row in cursor.fetchall()]
    conn.close()
    return reservados

def reservar_numero(numero, nome, contato, comprovante_path):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rifa (numero, nome, contato, comprovante) VALUES (%s, %s, %s, %s)",
                   (numero, nome, contato, comprovante_path))
    conn.commit()
    conn.close()

# ======== STREAMLIT ========

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
            path = ""
            if comprovante:
                pasta = "comprovantes"
                os.makedirs(pasta, exist_ok=True)
                path = os.path.join(pasta, f"{numero_selecionado}_{comprovante.name}")
                with open(path, "wb") as f:
                    f.write(comprovante.getbuffer())

            reservar_numero(numero_selecionado, nome.strip(), contato.strip(), path)
            st.success(f"Número {numero_selecionado} reservado com sucesso! ✅")
            st.balloons()
            del st.session_state["numero_selecionado"]
            st.rerun()
