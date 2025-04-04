import streamlit as st
import psycopg2
from supabase import create_client
import os

# # Expande a largura da página
# st.markdown("""
#     <style>
#         .main {
#             max-width: 100%;
#             padding-left: 3rem;
#             padding-right: 3rem;
#         }
#     </style>
# """, unsafe_allow_html=True)

# ======== CONEXÃO COM BANCO POSTGRES (SUPABASE) ========
def conectar():
    return psycopg2.connect(
        host="db.xkwusqpqmtjfehabofiv.supabase.co",
        database="postgres",
        user="postgres",
        password=st.secrets["DB_PASSWORD"],
        port="5432"
    )

# ======== CONEXÃO COM STORAGE SUPABASE (PRIVADO) ========
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======== INICIALIZAÇÃO DO BANCO ========
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

# ======== APP STREAMLIT ========
inicializar_banco()

if "limite_numeros" not in st.session_state:
    st.session_state["limite_numeros"] = 100

st.title("🎟️ Rifa Solidária - Prêmio R$200")



# ======== CABEÇALHO COM FOTO E MOTIVO ========
from PIL import Image

# ======== CABEÇALHO COM FOTO, TEXTO E QR CODE ========
st.markdown("---")
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    foto = Image.open("minha_foto.jpg")  # substitua pelo nome real da sua imagem
    st.image(foto, width=140, caption="Eduardo")

with col2:
    st.markdown("""
        <div style='font-size:18px; line-height:1.6'>
        Olá! Meu nome é <b>Eduardo</b>, sou doutorando em Engenharia de Produção na UFPE.<br>
        Estou organizando essa rifa porque estou <b>sem bolsa de estudo</b> no momento.<br>
        O valor arrecadado vai me ajudar com despesas acadêmicas e de subsistência.<br><br>
        🎁 O prêmio é <b>R$200</b> e cada número custa <b>R$10</b>.<br>
        🙏 Participe e me ajude a continuar meus estudos!\n
        💸 Chave Pix: eduardo.es@ufpe.br
        </div>
    """, unsafe_allow_html=True)

with col3:
    qr = Image.open("qrbanco.png")  # nome da imagem do QR Code Pix
    st.image(qr, width=140, caption="Chave Pix")


######################

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

if "mostrar_mais" not in st.session_state:
    st.session_state["mostrar_mais"] = False

if st.button("🔁 Ver mais números"):
    st.session_state["limite_numeros"] += 50
    st.session_state["mostrar_mais"] = True
    st.rerun()


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
                nome_arquivo = f"{numero_selecionado}_{comprovante.name}".replace("\\", "/")
                conteudo = comprovante.getvalue()

                try:
                    supabase.storage.from_("comprovantes").upload(
                        path=nome_arquivo,
                        file=conteudo,
                        file_options={"content-type": comprovante.type}
                    )
                    caminho = nome_arquivo
                except Exception as e:
                    st.warning("⚠️ Erro ao enviar o comprovante. Ele será ignorado.")

            reservar_numero(numero_selecionado, nome.strip(), contato.strip(), caminho)
            st.success(f"Número {numero_selecionado} reservado com sucesso! ✅")
            st.balloons()
            del st.session_state["numero_selecionado"]
            st.rerun()

# ======== ÁREA ADMINISTRATIVA COM BOTÃO DE LOGIN ========
st.markdown("## 👨‍💼 Acesso do administrador")

if "admin_autenticado" not in st.session_state:
    st.session_state["admin_autenticado"] = False

if not st.session_state["admin_autenticado"]:
    if st.button("🔐 Entrar como administrador"):
        st.session_state["mostrar_senha"] = True

    if st.session_state.get("mostrar_senha"):
        senha = st.text_input("Digite a senha", type="password")
        if senha == st.secrets["ADMIN_PASSWORD"]:  # troque pela sua senha real
            st.success("Login realizado com sucesso! ✅")
            st.session_state["admin_autenticado"] = True
            st.rerun()
        elif senha:
            st.error("Senha incorreta.")
else:
    st.success("✅ Você está logado como administrador.")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT numero, nome, contato, comprovante, data_reserva FROM rifa ORDER BY numero")
    reservas = cursor.fetchall()
    conn.close()

    for numero, nome, contato, arquivo, data in reservas:
        st.markdown(f"🔢 **{numero}** | {nome} ({contato}) – {data.strftime('%d/%m/%Y %H:%M')}")
        if arquivo:
            st.code(f"📁 Arquivo salvo: {arquivo}")
            try:
                signed_url = supabase.storage.from_("comprovantes").create_signed_url(arquivo, 60)
                st.markdown(f"[📎 Ver comprovante (válido por 1 min)]({signed_url['signedURL']})")
            except:
                st.warning("⚠️ Link do comprovante não pôde ser gerado.")
        st.markdown("---")
