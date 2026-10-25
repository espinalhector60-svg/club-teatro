from html import escape
import glob
import hashlib
import os
import hmac
from io import BytesIO
import re
from random import sample
import secrets
import time
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from firebase_admin import credentials, firestore, get_app, initialize_app
from firebase_admin.exceptions import FirebaseError
from google.api_core.exceptions import AlreadyExists, GoogleAPICallError
from google.cloud.firestore_v1.query import Query
from google.cloud.firestore_v1.transaction import transactional
from streamlit.errors import StreamlitSecretNotFoundError


st.set_page_config(
    page_title="Escena y Aprendizaje",
    page_icon="🎭",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Nunito:wght@600;700;800;900&display=swap');
    :root { --ink: #24212c; --muted: #797582; --purple: #8065c6; --pink: #f95fb4; }
    .stApp { background: #c6c5dc; color: var(--ink); font-family: 'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1500px;
        padding: 1.5rem 2.25rem 2.25rem;
        background: #fff;
        border: 1px solid #eeedf3;
        border-radius: 30px;
        margin: 1.25rem auto 2rem;
        box-shadow: 0 24px 70px #40355424;
    }
    h1, h2, h3, h4 { font-family: 'Nunito', sans-serif; color: var(--ink); letter-spacing: -.03em; }
    h1 { font-size: 2rem !important; }
    [data-testid="stCaptionContainer"] { color: #625d68; }
    [data-testid="stMetric"] {
        background: #fff;
        padding: 1rem 1.1rem;
        border: 1px solid #e9e3f2;
        border-radius: 20px;
        box-shadow: 0 8px 24px #4e426110;
    }
    [data-testid="stMetricLabel"] { color: #777280; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Nunito', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e9e3f2 !important;
        border-radius: 23px !important;
        background: #fff;
        box-shadow: 0 8px 25px #4e42610e;
    }
    [data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #7964c9, #f567b7); }
    .brand-mark {
        display: inline-flex; width: 48px; height: 48px; align-items: center; justify-content: center;
        border-radius: 16px; background: #fae1f4; font-size: 1.6rem; margin-right: .7rem;
    }
    .brand-title { font-family: 'Nunito', sans-serif; font-size: 1.1rem; font-weight: 900; }
    .nav-wrap { border-bottom: 1px solid #f0edf4; padding-bottom: .7rem; margin-bottom: 1.2rem; }
    .welcome-card {
        padding: 1.4rem 1.5rem; border-radius: 22px; color: #432c55;
        background: linear-gradient(120deg, #fbe2f3, #f0e8ff 70%, #e8f5ff);
        margin-bottom: 1rem;
    }
    .welcome-card p { color: #716278; margin: .25rem 0 0; }
    .tile { padding: 1.2rem 1.25rem; border-radius: 22px; min-height: 132px; }
    .tile .emoji { font-size: 1.3rem; }
    .tile .big { font: 900 2rem 'Nunito', sans-serif; margin-top: .35rem; }
    .tile .label { font-size: .84rem; color: #4b4651; }
    .tile-mint { background: #e3f5e4; }
    .tile-peach { background: #fff0dc; }
    .tile-lilac { background: #f2e2fa; }
    .section-eyebrow { color: #8b7c96; font-size: .76rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
    .rank-row { display: flex; justify-content: space-between; padding: .36rem 0; color: #625d68; font-size: .88rem; }
    .rank-row-active { color: #6d50b4; font-weight: 800; }
    .frame-label { text-align: center; font-weight: 800; color: #49366b; padding-top: .35rem; }
    .profile-photo { border-radius: 50%; }
    .stButton > button {
        border-radius: 13px; border: 0; font-weight: 800; min-height: 2.8rem;
        color: #49366b !important; background: #f1eafa !important;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 18px #8065c633; }
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(100deg, #7964c9, #e35daa) !important;
        color: #fff !important;
    }
    div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(100deg, #7059bd, #d94f9f) !important;
        border: 0 !important;
        color: #fff !important;
        font-weight: 800;
    }
    [data-testid="stRadio"] label {
        display: flex; align-items: center; min-height: 2.75rem;
        background: #faf8fc; border: 1px solid #eeeaf3; padding: .45rem .65rem;
        border-radius: 12px; color: #332d3a !important; opacity: 1 !important;
    }
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] [data-testid="stMarkdownContainer"] {
        color: #332d3a !important; opacity: 1 !important;
    }
    [data-testid="stTextInput"] input {
        color: #292431 !important; background: #fff !important;
        -webkit-text-fill-color: #292431 !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #8a8490 !important; -webkit-text-fill-color: #8a8490 !important; opacity: 1;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stTextInput"] label p,
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] label p {
        color: #393442 !important;
        opacity: 1 !important;
        font-weight: 700;
    }
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
        color: #332d3a !important;
        opacity: 1 !important;
    }
    [data-testid="stAlert"] {
        border: 1px solid #eadca0;
        border-radius: 15px;
        box-shadow: 0 5px 16px #4e42610a;
    }
    [data-testid="stExpander"] {
        border: 1px solid #eeeaf3;
        border-radius: 16px;
        background: #fff;
    }
    @media (max-width: 760px) {
        [data-testid="stMainBlockContainer"] { padding: .8rem; border-width: 3px; border-radius: 22px; margin: .4rem; }
    }
    .stTabs [data-baseweb="tab-list"] { gap: .4rem; }
    .stTabs [data-baseweb="tab"] { color: #514865; border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


QUESTIONS = [
    {
        "question": "¿Qué es un guion teatral?",
        "options": [
            "Un texto que organiza diálogos y acciones para una obra",
            "Una lista de canciones para el público",
            "Un plano del edificio del teatro",
            "Un comentario escrito después de la función",
        ],
        "answer": "Un texto que organiza diálogos y acciones para una obra",
        "explanation": "El guion reúne elementos como diálogos, personajes y acciones escénicas.",
    },
    {
        "question": "¿Quién interpreta un personaje en una obra?",
        "options": ["El actor o la actriz", "El tramoyista", "El espectador", "El apuntador solamente"],
        "answer": "El actor o la actriz",
        "explanation": "Quien actúa da vida al personaje mediante la voz, el cuerpo y la imaginación.",
    },
    {
        "question": "¿Cómo se llama el lugar donde actúan los intérpretes?",
        "options": ["Escenario", "Vestíbulo", "Taquilla", "Camerino"],
        "answer": "Escenario",
        "explanation": "El escenario es el espacio principal donde ocurre la acción teatral.",
    },
    {
        "question": "¿Qué indican normalmente las acotaciones de un guion?",
        "options": [
            "Movimientos, gestos o indicaciones de escena",
            "El precio de las entradas",
            "Los nombres de quienes compraron boletos",
            "La duración del recreo",
        ],
        "answer": "Movimientos, gestos o indicaciones de escena",
        "explanation": "Las acotaciones orientan la puesta en escena y suelen distinguirse de los diálogos.",
    },
    {
        "question": "¿Qué es el diálogo en una obra teatral?",
        "options": [
            "La conversación entre dos o más personajes",
            "La lista de objetos del escenario",
            "La música de cierre",
            "El saludo del público",
        ],
        "answer": "La conversación entre dos o más personajes",
        "explanation": "Los diálogos permiten que los personajes se comuniquen y hagan avanzar la acción.",
    },
    {
        "question": "¿Qué hace principalmente la persona que dirige una obra?",
        "options": [
            "Coordina la interpretación y las decisiones de puesta en escena",
            "Vende todas las entradas",
            "Escribe cada reseña del público",
            "Permanece como personaje en todas las escenas",
        ],
        "answer": "Coordina la interpretación y las decisiones de puesta en escena",
        "explanation": "La dirección ayuda a unificar el trabajo artístico y escénico.",
    },
    {
        "question": "¿Para qué sirve el vestuario teatral?",
        "options": [
            "Ayuda a comunicar quién es el personaje y en qué mundo vive",
            "Reemplaza el texto del guion",
            "Evita que el público escuche",
            "Se usa solo para decorar el telón",
        ],
        "answer": "Ayuda a comunicar quién es el personaje y en qué mundo vive",
        "explanation": "La ropa y los accesorios pueden dar pistas sobre época, profesión o personalidad.",
    },
    {
        "question": "¿Qué es la escenografía?",
        "options": [
            "El diseño del espacio visual donde sucede la obra",
            "La lista de espectadores",
            "El ensayo de pronunciación",
            "La venta de programas",
        ],
        "answer": "El diseño del espacio visual donde sucede la obra",
        "explanation": "La escenografía ayuda a crear el lugar y la atmósfera de la historia.",
    },
    {
        "question": "¿Qué puede aportar la iluminación en una escena?",
        "options": [
            "Crear ambiente y dirigir la atención",
            "Cambiar las palabras del guion automáticamente",
            "Sustituir a todos los personajes",
            "Indicar el precio de la función",
        ],
        "answer": "Crear ambiente y dirigir la atención",
        "explanation": "La luz puede sugerir una hora, un estado de ánimo o destacar una acción.",
    },
    {
        "question": "¿Qué es un ensayo teatral?",
        "options": [
            "Una práctica para preparar la obra antes de presentarla",
            "Una función abierta al público",
            "Una pausa durante la obra",
            "Un tipo de entrada",
        ],
        "answer": "Una práctica para preparar la obra antes de presentarla",
        "explanation": "En los ensayos se trabajan el texto, los movimientos y la coordinación.",
    },
    {
        "question": "¿Qué significa improvisar en teatro?",
        "options": [
            "Crear una respuesta o acción en el momento, respetando la situación",
            "Leer siempre el final de la obra",
            "Abandonar el escenario sin motivo",
            "Repetir una escena sin escuchar a nadie",
        ],
        "answer": "Crear una respuesta o acción en el momento, respetando la situación",
        "explanation": "La improvisación entrena la creatividad y la escucha entre participantes.",
    },
    {
        "question": "¿Qué es el conflicto dramático?",
        "options": [
            "Un problema o deseo que impulsa la acción de la historia",
            "Una discusión real entre el elenco",
            "El cambio de decorado",
            "El aplauso final",
        ],
        "answer": "Un problema o deseo que impulsa la acción de la historia",
        "explanation": "El conflicto crea retos que los personajes intentan resolver.",
    },
    {
        "question": "¿Quién es el público?",
        "options": [
            "Las personas que observan la representación",
            "El equipo que construye el escenario",
            "Los personajes de la historia",
            "La persona que escribe el programa",
        ],
        "answer": "Las personas que observan la representación",
        "explanation": "El público participa como espectador y recibe la historia presentada.",
    },
    {
        "question": "¿Qué es una escena?",
        "options": [
            "Una parte de la obra que ocurre en una situación o momento determinado",
            "El edificio completo del teatro",
            "El vestuario de un personaje",
            "La invitación a la función",
        ],
        "answer": "Una parte de la obra que ocurre en una situación o momento determinado",
        "explanation": "Las escenas organizan la acción en partes comprensibles.",
    },
    {
        "question": "¿Qué suele marcar un cambio de acto?",
        "options": [
            "Una división importante en la estructura de la obra",
            "El cambio de asiento del público",
            "La entrada de cada espectador",
            "El inicio de un ensayo",
        ],
        "answer": "Una división importante en la estructura de la obra",
        "explanation": "Los actos son divisiones amplias que agrupan partes de una obra.",
    },
    {
        "question": "¿Qué es un monólogo?",
        "options": [
            "Un parlamento extenso dicho por un solo personaje",
            "Una conversación entre todo el público",
            "Un cambio de escenografía",
            "Una canción sin intérprete",
        ],
        "answer": "Un parlamento extenso dicho por un solo personaje",
        "explanation": "En un monólogo, un personaje expresa sus ideas o sentimientos durante un tiempo.",
    },
    {
        "question": "¿Qué es un personaje?",
        "options": [
            "Un ser representado dentro de la historia",
            "Una luz que ilumina el escenario",
            "Un asiento del teatro",
            "Una indicación para vender entradas",
        ],
        "answer": "Un ser representado dentro de la historia",
        "explanation": "Los personajes realizan acciones y se relacionan en la obra.",
    },
    {
        "question": "¿Qué caracteriza a un protagonista?",
        "options": [
            "Tiene un papel central en el desarrollo de la historia",
            "Siempre es quien diseña las luces",
            "Nunca habla en la obra",
            "Es necesariamente la persona más graciosa",
        ],
        "answer": "Tiene un papel central en el desarrollo de la historia",
        "explanation": "La historia suele seguir de cerca los objetivos y desafíos del protagonista.",
    },
    {
        "question": "¿Qué es un antagonista?",
        "options": [
            "Un personaje o fuerza que se opone al objetivo de otro",
            "La persona que acomoda las sillas",
            "El público de la última fila",
            "Quien prepara el vestuario",
        ],
        "answer": "Un personaje o fuerza que se opone al objetivo de otro",
        "explanation": "La oposición crea obstáculos; el antagonista no tiene que ser siempre malvado.",
    },
    {
        "question": "¿Qué es una utilería?",
        "options": [
            "Los objetos que se usan durante la representación",
            "La lista de diálogos",
            "El plano de las butacas",
            "El saludo de despedida",
        ],
        "answer": "Los objetos que se usan durante la representación",
        "explanation": "La utilería puede incluir objetos que los personajes manipulan en escena.",
    },
    {
        "question": "¿Qué hace el equipo de tramoya?",
        "options": [
            "Ayuda a mover o cambiar elementos escénicos",
            "Escribe todas las críticas",
            "Dirige al público durante los diálogos",
            "Interpreta siempre al personaje principal",
        ],
        "answer": "Ayuda a mover o cambiar elementos escénicos",
        "explanation": "La tramoya colabora con los cambios técnicos y escenográficos.",
    },
    {
        "question": "¿Qué es un telón?",
        "options": [
            "Una cortina que puede abrir o cerrar la vista del escenario",
            "Una página del guion",
            "Una lámpara portátil",
            "Una prenda del vestuario",
        ],
        "answer": "Una cortina que puede abrir o cerrar la vista del escenario",
        "explanation": "El telón puede señalar el comienzo, el final o una transición.",
    },
    {
        "question": "¿Qué significa hablar con proyección en el escenario?",
        "options": [
            "Usar la voz para que se escuche con claridad sin gritar",
            "Hablar mirando siempre al suelo",
            "Decir el texto lo más rápido posible",
            "Susurrar todas las frases",
        ],
        "answer": "Usar la voz para que se escuche con claridad sin gritar",
        "explanation": "La proyección vocal permite llegar al público cuidando la voz.",
    },
    {
        "question": "¿Qué ayuda a que el público comprenda mejor las palabras?",
        "options": [
            "La buena dicción y la articulación",
            "Hablar de espaldas todo el tiempo",
            "Taparse la boca",
            "Acelerar todas las frases",
        ],
        "answer": "La buena dicción y la articulación",
        "explanation": "Pronunciar con claridad facilita que el público siga el diálogo.",
    },
    {
        "question": "¿Qué es la expresión corporal?",
        "options": [
            "Comunicar ideas o emociones con el cuerpo y los gestos",
            "Escribir las acotaciones",
            "Elegir los asientos",
            "Pintar el telón",
        ],
        "answer": "Comunicar ideas o emociones con el cuerpo y los gestos",
        "explanation": "La postura, los movimientos y los gestos también cuentan la historia.",
    },
    {
        "question": "¿Por qué es importante escuchar a las compañeras y compañeros en escena?",
        "options": [
            "Para responder con atención y coordinarse",
            "Para terminar antes de tiempo",
            "Para ignorar las señales de escena",
            "Para memorizar el papel de otra persona",
        ],
        "answer": "Para responder con atención y coordinarse",
        "explanation": "La escucha activa hace que las interacciones se sientan naturales y seguras.",
    },
    {
        "question": "¿Qué es una puesta en escena?",
        "options": [
            "La organización de los elementos para presentar una obra",
            "El resumen que se entrega al salir",
            "El edificio donde se guardan las entradas",
            "La lista de tareas del público",
        ],
        "answer": "La organización de los elementos para presentar una obra",
        "explanation": "Incluye decisiones de actuación, espacio, ritmo, vestuario y otros elementos.",
    },
    {
        "question": "¿Qué puede indicar una pausa durante un diálogo?",
        "options": [
            "Una emoción, una duda o un momento para dar énfasis",
            "Que la obra terminó necesariamente",
            "Que el público debe abandonar la sala",
            "Que el personaje olvidó toda la historia",
        ],
        "answer": "Una emoción, una duda o un momento para dar énfasis",
        "explanation": "El silencio también puede ser una herramienta expresiva.",
    },
    {
        "question": "¿Qué es el ritmo de una escena?",
        "options": [
            "La velocidad y energía con que se desarrolla la acción",
            "La cantidad de sillas disponibles",
            "El número de páginas del programa",
            "La altura del telón",
        ],
        "answer": "La velocidad y energía con que se desarrolla la acción",
        "explanation": "El ritmo puede variar para crear tensión, calma o sorpresa.",
    },
    {
        "question": "¿Qué es una adaptación teatral?",
        "options": [
            "Una versión de una historia preparada para ser representada",
            "Un ensayo de iluminación",
            "Una lista de espectadores",
            "Una reparación del escenario",
        ],
        "answer": "Una versión de una historia preparada para ser representada",
        "explanation": "Al adaptar, se toman decisiones para llevar una historia al lenguaje escénico.",
    },
    {
        "question": "¿Qué es el espacio escénico?",
        "options": [
            "El área donde se desarrolla la acción teatral",
            "La fila donde se sienta el público",
            "La entrada principal del teatro",
            "La mesa de venta de boletos",
        ],
        "answer": "El área donde se desarrolla la acción teatral",
        "explanation": "El espacio escénico puede ser un escenario tradicional o cualquier lugar transformado.",
    },
    {
        "question": "¿Qué es una cuarta pared en la convención teatral?",
        "options": [
            "La pared imaginaria entre los personajes y el público",
            "Una pared detrás del camerino",
            "El fondo de una escenografía",
            "Una puerta de emergencia",
        ],
        "answer": "La pared imaginaria entre los personajes y el público",
        "explanation": "En algunas obras los personajes actúan como si el público no estuviera allí.",
    },
    {
        "question": "¿Qué ocurre cuando una obra rompe la cuarta pared?",
        "options": [
            "Los personajes reconocen o se dirigen al público",
            "Se destruye una pared real",
            "Se apagan todas las luces",
            "El público pasa a ser el equipo técnico",
        ],
        "answer": "Los personajes reconocen o se dirigen al público",
        "explanation": "Es una convención que establece contacto directo entre escena y espectadores.",
    },
    {
        "question": "¿Qué es una comedia?",
        "options": [
            "Una obra que suele presentar situaciones humorísticas",
            "Una obra sin personajes",
            "Una función sin diálogos ni acciones",
            "Una obra que siempre termina de forma triste",
        ],
        "answer": "Una obra que suele presentar situaciones humorísticas",
        "explanation": "La comedia busca divertir y puede también invitar a reflexionar.",
    },
    {
        "question": "¿Qué suele buscar la tragedia como género teatral?",
        "options": [
            "Presentar conflictos graves y sus consecuencias",
            "Enseñar únicamente pasos de baile",
            "Evitar cualquier problema en la historia",
            "Mostrar solo escenas de juegos",
        ],
        "answer": "Presentar conflictos graves y sus consecuencias",
        "explanation": "La tragedia explora conflictos intensos y decisiones difíciles.",
    },
    {
        "question": "¿Qué es el teatro de títeres?",
        "options": [
            "Una representación donde se animan muñecos o figuras",
            "Una obra representada solo por narradores sentados",
            "Una lectura en silencio",
            "Un concierto sin personajes",
        ],
        "answer": "Una representación donde se animan muñecos o figuras",
        "explanation": "Los títeres pueden manipularse con las manos, varillas, hilos u otras técnicas.",
    },
    {
        "question": "¿Qué significa que un personaje tenga un objetivo?",
        "options": [
            "Que quiere conseguir algo dentro de la historia",
            "Que conoce el horario del teatro",
            "Que diseñó el vestuario",
            "Que siempre debe ganar",
        ],
        "answer": "Que quiere conseguir algo dentro de la historia",
        "explanation": "El objetivo ayuda a comprender por qué el personaje actúa de cierta manera.",
    },
    {
        "question": "¿Qué puede ser un subtexto en una escena?",
        "options": [
            "Lo que un personaje piensa o siente más allá de sus palabras",
            "El título impreso en una entrada",
            "Una nota para ordenar el vestuario",
            "El texto que aparece en una cartelera",
        ],
        "answer": "Lo que un personaje piensa o siente más allá de sus palabras",
        "explanation": "El subtexto agrega significado a lo que se dice o se calla.",
    },
    {
        "question": "¿Qué es un cambio de escena?",
        "options": [
            "Una transición que modifica el lugar, el momento o la situación",
            "La salida definitiva del público",
            "El cambio de opinión de quien dirige",
            "La elección de una entrada",
        ],
        "answer": "Una transición que modifica el lugar, el momento o la situación",
        "explanation": "Los cambios pueden señalar que la historia pasa a otro espacio o momento.",
    },
    {
        "question": "¿Para qué sirve la música en una representación?",
        "options": [
            "Puede crear ambiente, acompañar acciones o marcar transiciones",
            "Para reemplazar obligatoriamente a todos los diálogos",
            "Para impedir que se vea el escenario",
            "Para indicar el número de actores",
        ],
        "answer": "Puede crear ambiente, acompañar acciones o marcar transiciones",
        "explanation": "La música es un recurso expresivo que se integra según las necesidades de la obra.",
    },
    {
        "question": "¿Qué es una entrada teatral?",
        "options": [
            "El momento en que un personaje aparece en escena",
            "La salida del edificio",
            "El descanso del elenco",
            "La primera página del guion",
        ],
        "answer": "El momento en que un personaje aparece en escena",
        "explanation": "Las entradas y salidas organizan quién está presente en cada momento.",
    },
    {
        "question": "¿Qué es una salida teatral?",
        "options": [
            "El momento en que un personaje deja el espacio escénico",
            "El final de la venta de boletos",
            "La pausa del público",
            "El inicio de la música",
        ],
        "answer": "El momento en que un personaje deja el espacio escénico",
        "explanation": "Las salidas deben estar coordinadas con la acción y las indicaciones de escena.",
    },
    {
        "question": "¿Qué es el maquillaje teatral?",
        "options": [
            "Un recurso para transformar o resaltar rasgos del personaje",
            "Un tipo de iluminación",
            "Una parte del telón",
            "Un método para aprender diálogos",
        ],
        "answer": "Un recurso para transformar o resaltar rasgos del personaje",
        "explanation": "El maquillaje puede ayudar a que los rasgos se vean desde distintas distancias.",
    },
    {
        "question": "¿Qué es la caracterización?",
        "options": [
            "El conjunto de recursos que construyen la identidad de un personaje",
            "El inventario de butacas",
            "La limpieza del escenario",
            "La lista de escenas sin orden",
        ],
        "answer": "El conjunto de recursos que construyen la identidad de un personaje",
        "explanation": "La voz, el cuerpo, el vestuario y las decisiones de actuación ayudan a caracterizar.",
    },
    {
        "question": "¿Qué ayuda a mantener la seguridad durante un ensayo?",
        "options": [
            "Respetar el espacio, las señales y los acuerdos del grupo",
            "Correr entre objetos sin avisar",
            "Mover equipos eléctricos sin autorización",
            "Cambiar movimientos sin comunicarlo",
        ],
        "answer": "Respetar el espacio, las señales y los acuerdos del grupo",
        "explanation": "La seguridad y el cuidado mutuo son parte importante del trabajo escénico.",
    },
    {
        "question": "¿Qué es el trabajo en equipo en una obra?",
        "options": [
            "Colaborar para que las distintas partes de la función se integren",
            "Hacer todas las tareas sin escuchar a nadie",
            "Competir para hablar más que el resto",
            "Dejar la preparación a una sola persona",
        ],
        "answer": "Colaborar para que las distintas partes de la función se integren",
        "explanation": "Actuación y trabajo técnico se apoyan para hacer posible la representación.",
    },
    {
        "question": "¿Qué es la memoria escénica?",
        "options": [
            "Recordar texto, movimientos y señales de una escena",
            "Guardar entradas antiguas",
            "Memorizar los nombres del público",
            "Aprender solo el título de la obra",
        ],
        "answer": "Recordar texto, movimientos y señales de una escena",
        "explanation": "La práctica ayuda a integrar el texto y las acciones con confianza.",
    },
    {
        "question": "¿Qué es una señal escénica o cue?",
        "options": [
            "Una indicación para iniciar una acción o un efecto",
            "Una reseña escrita por un espectador",
            "El nombre de una butaca",
            "Una parte del vestuario",
        ],
        "answer": "Una indicación para iniciar una acción o un efecto",
        "explanation": "Las señales coordinan entradas, sonidos, luces y otros momentos de la función.",
    },
    {
        "question": "¿Qué es una lectura dramatizada?",
        "options": [
            "Leer los diálogos interpretando voces e intenciones",
            "Construir una escenografía completa",
            "Presentar una obra sin texto",
            "Leer en silencio el programa de mano",
        ],
        "answer": "Leer los diálogos interpretando voces e intenciones",
        "explanation": "La lectura dramatizada permite explorar una obra sin montar toda la producción.",
    },
    {
        "question": "¿Qué puede comunicar el tono de voz de un personaje?",
        "options": [
            "Emociones, intenciones y relaciones",
            "El color del telón",
            "La cantidad de asientos",
            "El precio de la entrada",
        ],
        "answer": "Emociones, intenciones y relaciones",
        "explanation": "El tono cambia cómo se entiende una frase y qué siente el personaje.",
    },
]

def load_questions():
    app_directory = os.path.dirname(os.path.abspath(__file__))
    question_files = [
        file_path
        for file_path in glob.glob(os.path.join(app_directory, "*.txt"))
        if os.path.basename(file_path).lower() != "requirements.txt"
    ]
    if len(question_files) != 1:
        raise FileNotFoundError(
            "Coloca el archivo TXT de preguntas en la misma carpeta que tareascolar.py."
        )

    with open(question_files[0], encoding="utf-8-sig") as question_file:
        content = question_file.read()
    matches = list(re.finditer(r"(?m)^(\d+)\.\s*(.+?)\s*$", content))
    questions = []
    seen_numbers = set()

    for index, question_match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        block = content[question_match.end():end]
        options = dict(re.findall(r"(?m)^([A-D])\)\s*(.+?)\s*$", block))
        answer_match = re.search(r"(?m)^Respuesta correcta:\s*([A-D])\s*$", block)
        number = int(question_match.group(1))
        if number in seen_numbers or set(options) != set("ABCD") or len(set(options.values())) != 4:
            raise ValueError(f"La pregunta {number} del archivo está incompleta o repetida.")
        if answer_match is None:
            raise ValueError(f"Falta la respuesta correcta de la pregunta {number}.")

        correct_answer = options[answer_match.group(1)]
        questions.append(
            {
                "number": number,
                "question": question_match.group(2),
                "options": [options[letter] for letter in "ABCD"],
                "answer": correct_answer,
                "explanation": f"La respuesta correcta indicada en el material es: {correct_answer}",
            }
        )
        seen_numbers.add(number)

    if not questions:
        raise ValueError("No se encontraron preguntas en el archivo de texto.")

    return sorted(questions, key=lambda question: question["number"])

def mezclar_opciones(preguntas):
    posiciones_correctas = sample(
        [indice % 4 for indice in range(len(preguntas))],
        len(preguntas),
    )
    preguntas_mezcladas = []
    for pregunta, posicion_correcta in zip(preguntas, posiciones_correctas):
        distractores = [
            opcion for opcion in pregunta["options"] if opcion != pregunta["answer"]
        ]
        opciones = sample(distractores, len(distractores))
        opciones.insert(posicion_correcta, pregunta["answer"])
        preguntas_mezcladas.append({**pregunta, "options": opciones})
    return preguntas_mezcladas


QUESTIONS = load_questions()

DIFICULTAD_INDICES = {
    "Fácil": range(0, len(QUESTIONS) // 3),
    "Normal": range(len(QUESTIONS) // 3, 2 * len(QUESTIONS) // 3),
    "Difícil": range(2 * len(QUESTIONS) // 3, len(QUESTIONS)),
}

RANGOS = [
    {"nombre": "Normal", "minimo": 0, "insignia": "🎭"},
    {"nombre": "Raro", "minimo": 20, "insignia": "🌟"},
    {"nombre": "Plata", "minimo": 50, "insignia": "🥈"},
    {"nombre": "Oro", "minimo": 100, "insignia": "🥇"},
    {"nombre": "Épico", "minimo": 160, "insignia": "🔥"},
    {"nombre": "Diamante", "minimo": 240, "insignia": "💎"},
    {"nombre": "Mítico", "minimo": 340, "insignia": "🌙"},
    {"nombre": "Reina", "minimo": 460, "insignia": "👑"},
]

MARCOS = [
    {"nombre": "Normal", "minimo": 0, "precio": 0, "color": "#e974a7", "detalle": "Kawaii floral", "archivo": "normal"},
    {"nombre": "Raro", "minimo": 20, "precio": 6, "color": "#a76adb", "detalle": "Mariposas", "archivo": "raro"},
    {"nombre": "Plata", "minimo": 50, "precio": 14, "color": "#a5a8b2", "detalle": "Estrellas plateadas", "archivo": "plata"},
    {"nombre": "Oro", "minimo": 100, "precio": 28, "color": "#e9b63d", "detalle": "Dorado real", "archivo": "oro"},
    {"nombre": "Épico", "minimo": 160, "precio": 42, "color": "#9254cb", "detalle": "Estrellas épicas", "archivo": "epico"},
    {"nombre": "Diamante", "minimo": 240, "precio": 60, "color": "#38aee5", "detalle": "Cristales", "archivo": "diamante"},
    {"nombre": "Mítico", "minimo": 340, "precio": 82, "color": "#543582", "detalle": "Luna y noche", "archivo": "mitico"},
    {"nombre": "Reina", "minimo": 460, "precio": 110, "color": "#df67ae", "detalle": "Corona real", "archivo": "reina"},
]


def obtener_rango(puntos):
    rango_actual = RANGOS[0]
    for rango in RANGOS:
        if puntos >= rango["minimo"]:
            rango_actual = rango
        else:
            break
    return rango_actual


def crear_foto_con_marco(foto_bytes, marco):
    ruta_marco = Path(__file__).parent / "assets" / "marcos" / f"{marco['archivo']}.png"
    escala = 3
    imagen_marco = Image.open(ruta_marco).convert("RGBA")
    imagen_marco = imagen_marco.resize(
        (imagen_marco.width * escala, imagen_marco.height * escala),
        Image.Resampling.LANCZOS,
    )
    imagen_marco = imagen_marco.filter(
        ImageFilter.UnsharpMask(radius=2.2, percent=145, threshold=3)
    )
    abertura = tuple(coordenada * escala for coordenada in (39, 99, 171, 268))
    ancho = abertura[2] - abertura[0]
    alto = abertura[3] - abertura[1]
    if foto_bytes is None:
        recorte = Image.new("RGBA", (ancho, alto), "#f5eafa")
        silueta = ImageDraw.Draw(recorte)
        silueta.ellipse(
            (34 * escala, 10 * escala, ancho - 34 * escala, 94 * escala),
            fill="#f3c5a8",
        )
        silueta.ellipse(
            (12 * escala, 90 * escala, ancho - 12 * escala, alto + 32 * escala),
            fill=marco["color"],
        )
    else:
        try:
            foto = Image.open(BytesIO(foto_bytes)).convert("RGB")
        except (OSError, ValueError) as error:
            raise ValueError(
                "No se pudo leer la imagen. Elige un archivo JPG, PNG o WEBP válido."
            ) from error
        recorte = ImageOps.fit(foto, (ancho, alto), method=Image.Resampling.LANCZOS)

    mascara = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, ancho - 1, alto - 1),
        radius=15 * escala,
        fill=255,
    )
    imagen_marco.paste(recorte.convert("RGBA"), (abertura[0], abertura[1]), mascara)
    return imagen_marco


def normalizar_apodo(apodo):
    return " ".join(apodo.split()).casefold()


def validar_apodo(apodo):
    return bool(re.fullmatch(r"[\w .-]{3,24}", apodo, flags=re.UNICODE))


def id_alumna(apodo):
    return hashlib.sha256(normalizar_apodo(apodo).encode("utf-8")).hexdigest()


def hash_pin(pin, sal):
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        bytes.fromhex(sal),
        180_000,
    ).hex()


@st.cache_resource
def obtener_firestore():
    try:
        cuenta = dict(st.secrets["firebase_service_account"])
    except (KeyError, StreamlitSecretNotFoundError):
        return None

    try:
        aplicacion = get_app("club_teatro")
    except ValueError:
        aplicacion = initialize_app(
            credentials.Certificate(cuenta),
            name="club_teatro",
        )
    return firestore.client(app=aplicacion)


def guardar_perfil_remoto(db):
    if db is None or not st.session_state.usuario_id:
        return
    db.collection("alumnas").document(st.session_state.usuario_id).set(
        {
            "apodo": st.session_state.nombre_alumna,
            "puntos": st.session_state.puntos,
            "puntos_disponibles": st.session_state.puntos_disponibles,
            "respuestas_correctas": st.session_state.respuestas_correctas,
            "respuestas_respondidas": st.session_state.respuestas_respondidas,
            "marcos_propios": st.session_state.marcos_propios,
            "marco_actual": st.session_state.marco_actual,
        },
        merge=True,
    )


def cargar_perfil_en_sesion(apodo, documento_id, perfil, compartido):
    st.session_state.nombre_alumna = apodo
    st.session_state.usuario_id = documento_id
    st.session_state.perfil_compartido = compartido
    st.session_state.foto_perfil = None
    st.session_state.puntos = int(perfil.get("puntos", 0))
    st.session_state.puntos_disponibles = int(perfil.get("puntos_disponibles", 0))
    st.session_state.respuestas_correctas = int(perfil.get("respuestas_correctas", 0))
    st.session_state.respuestas_respondidas = int(perfil.get("respuestas_respondidas", 0))
    marcos = perfil.get("marcos_propios", ["Normal"])
    st.session_state.marcos_propios = marcos if isinstance(marcos, list) else ["Normal"]
    st.session_state.marco_actual = perfil.get("marco_actual", "Normal")
    st.session_state.marco_actual = (
        st.session_state.marco_actual
        if st.session_state.marco_actual in st.session_state.marcos_propios
        else "Normal"
    )
    st.session_state.pagina = "Inicio"


def pin_valido(pin):
    return len(pin) == 6 and pin.isascii() and pin.isdigit()


def perfil_nuevo(apodo, pin):
    sal = secrets.token_hex(16)
    return {
        "apodo": " ".join(apodo.split()),
        "apodo_normalizado": normalizar_apodo(apodo),
        "pin_sal": sal,
        "pin_hash": hash_pin(pin, sal),
        "fallos_pin": 0,
        "bloqueado_hasta": 0,
        "puntos": 0,
        "puntos_disponibles": 0,
        "respuestas_correctas": 0,
        "respuestas_respondidas": 0,
        "marcos_propios": ["Normal"],
        "marco_actual": "Normal",
    }


def registrar_alumna(db, apodo, pin):
    documento_id = id_alumna(apodo)
    perfil = perfil_nuevo(apodo, pin)
    db.collection("alumnas").document(documento_id).create(perfil)
    return documento_id, perfil


def autenticar_alumna(db, apodo, pin):
    documento_id = id_alumna(apodo)
    referencia = db.collection("alumnas").document(documento_id)
    instantanea = referencia.get()
    if not instantanea.exists:
        return None, "No encontramos ese apodo. Revisa que esté escrito igual o crea una cuenta."

    perfil = instantanea.to_dict()
    bloqueado_hasta = int(perfil.get("bloqueado_hasta", 0))
    ahora = int(time.time())
    if bloqueado_hasta > ahora:
        minutos = max(1, (bloqueado_hasta - ahora + 59) // 60)
        return None, f"Demasiados intentos. Espera {minutos} minuto(s) e inténtalo de nuevo."

    sal = perfil.get("pin_sal", "")
    pin_guardado = perfil.get("pin_hash", "")
    pin_correcto = bool(sal and pin_guardado) and hmac.compare_digest(
        hash_pin(pin, sal),
        pin_guardado,
    )
    if not pin_correcto:
        fallos = int(perfil.get("fallos_pin", 0)) + 1
        referencia.update(
            {
                "fallos_pin": 0 if fallos >= 5 else fallos,
                "bloqueado_hasta": ahora + 300 if fallos >= 5 else 0,
            }
        )
        if fallos >= 5:
            return None, "Demasiados intentos. La cuenta queda bloqueada durante 5 minutos."
        return None, f"PIN incorrecto. Te quedan {5 - fallos} intento(s) antes del bloqueo temporal."

    referencia.update({"fallos_pin": 0, "bloqueado_hasta": 0})
    return (documento_id, perfil), None


def renombrar_alumna(db, documento_anterior, nuevo_apodo):
    documento_nuevo = id_alumna(nuevo_apodo)
    referencia_anterior = db.collection("alumnas").document(documento_anterior)
    referencia_nueva = db.collection("alumnas").document(documento_nuevo)
    if documento_anterior == documento_nuevo:
        referencia_anterior.update({"apodo": " ".join(nuevo_apodo.split())})
        return documento_anterior, True

    @transactional
    def mover_perfil(transaccion):
        perfil_anterior = transaccion.get(referencia_anterior)
        perfil_nuevo_snapshot = transaccion.get(referencia_nueva)
        if not perfil_anterior.exists or perfil_nuevo_snapshot.exists:
            return False
        datos = perfil_anterior.to_dict()
        datos["apodo"] = " ".join(nuevo_apodo.split())
        datos["apodo_normalizado"] = normalizar_apodo(nuevo_apodo)
        transaccion.create(referencia_nueva, datos)
        transaccion.delete(referencia_anterior)
        return True

    resultado = mover_perfil(db.transaction())
    return (documento_nuevo if resultado else documento_anterior), resultado


def crear_ranking(db):
    documentos = (
        db.collection("alumnas")
        .order_by("puntos", direction=Query.DESCENDING)
        .limit(500)
        .stream()
    )
    ranking = []
    total_aciertos = 0
    for documento in documentos:
        perfil = documento.to_dict()
        puntos = int(perfil.get("puntos", 0))
        total_aciertos += int(perfil.get("respuestas_correctas", 0))
        ranking.append((perfil.get("apodo", "Artista"), puntos))
    ranking.sort(key=lambda elemento: elemento[1], reverse=True)
    return ranking[:20], len(ranking), total_aciertos


try:
    DB_COMPARTIDA = obtener_firestore()
    ERROR_FIRESTORE = None
except (FirebaseError, GoogleAPICallError, OSError, ValueError, KeyError) as error:
    DB_COMPARTIDA = None
    ERROR_FIRESTORE = str(error)


for clave, valor in {
    "nombre_alumna": "",
    "usuario_id": "",
    "perfil_compartido": False,
    "puntos": 0,
    "puntos_disponibles": 0,
    "respuestas_correctas": 0,
    "respuestas_respondidas": 0,
    "marcos_propios": ["Normal"],
    "marco_actual": "Normal",
    "foto_perfil": None,
    "pagina": "Inicio",
    "quiz_activo": False,
    "quiz_terminado": False,
    "preguntas_ronda": [],
    "indice_pregunta": 0,
    "ronda": 0,
    "respuesta_revisada": False,
    "ultima_respuesta": None,
    "nivel_dificultad": "Normal",
    "error_cuenta": "",
}.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor

st.markdown(
    """
    <div style="height: 1rem"></div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.nombre_alumna:
    izquierda, bienvenida = st.columns([1.05, 1], gap="large", vertical_alignment="center")
    with izquierda:
        st.markdown("## Un escenario para aprender, imaginar y brillar ✨")
        st.write("Practica teatro, gana puntos y crea tu propio perfil de artista.")
        st.markdown(
            """
            <div class="tile tile-lilac">
              <div class="emoji">🎬 &nbsp; 💡 &nbsp; 🎭</div>
              <div class="big">Tu historia empieza aquí</div>
              <div class="label">{len(QUESTIONS)} preguntas · retos aleatorios · marcos para desbloquear</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with bienvenida:
        with st.container(border=True):
            st.markdown("### ¡Bienvenida al club!")
            if DB_COMPARTIDA is None:
                if ERROR_FIRESTORE:
                    st.error(f"No se pudo conectar al ranking compartido: {ERROR_FIRESTORE}")
                else:
                    st.warning(
                        "El ranking compartido todavía no está conectado. "
                        "Puedes probar la app en modo local; tu avance no se sincronizará."
                    )
                with st.form("formulario_apodo_local"):
                    apodo_local = st.text_input(
                        "Tu apodo",
                        max_chars=24,
                        placeholder="Ejemplo: EstrellaTeatral",
                    )
                    entrar_local = st.form_submit_button(
                        "Probar en este dispositivo",
                        type="primary",
                        use_container_width=True,
                    )
                if entrar_local:
                    apodo_local = (apodo_local or "").strip()
                    if not validar_apodo(apodo_local):
                        st.warning("El apodo debe tener entre 3 y 24 caracteres.")
                    else:
                        cargar_perfil_en_sesion(
                            apodo_local,
                            "",
                            {},
                            compartido=False,
                        )
                        st.rerun()
                with st.expander("¿Cómo activo las cuentas y el ranking compartidos?"):
                    st.markdown(
                        """
                        1. Crea un proyecto gratuito en [Firebase Console](https://console.firebase.google.com/).
                        2. Crea una base **Cloud Firestore** en modo producción.
                        3. En Configuración del proyecto → Cuentas de servicio, genera una clave privada.
                        4. No compartas esa clave ni la subas a GitHub. Crea `.streamlit/secrets.toml`
                           junto a `tareascolar.py` y pega sus campos con el formato indicado al final.
                        5. Ejecuta de nuevo la app. Las cuentas usarán apodo y PIN; el ranking solo
                           mostrará apodos y puntos.
                        """
                    )
                    st.code(
                        '[firebase_service_account]\n'
                        'type = "service_account"\n'
                        'project_id = "ID_DE_TU_PROYECTO"\n'
                        'private_key_id = "ID_DE_LA_CLAVE"\n'
                        'private_key = """-----BEGIN PRIVATE KEY-----\\nPEGA_AQUI_LA_CLAVE\\n-----END PRIVATE KEY-----\\n"""\n'
                        'client_email = "CUENTA_DE_SERVICIO"\n'
                        'client_id = "ID_DE_CLIENTE"\n'
                        'auth_uri = "https://accounts.google.com/o/oauth2/auth"\n'
                        'token_uri = "https://oauth2.googleapis.com/token"\n'
                        'auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\n'
                        'client_x509_cert_url = "URL_DEL_CERTIFICADO"\n'
                        'universe_domain = "googleapis.com"',
                        language="toml",
                    )
            else:
                registro_tab, ingreso_tab = st.tabs(["Crear cuenta", "Ya tengo cuenta"])
                with registro_tab:
                    st.caption("Usa un apodo, no tu nombre real. El PIN no se guarda en texto visible.")
                    with st.form("form_registro_compartido"):
                        apodo_nuevo = st.text_input("Apodo", max_chars=24)
                        pin_nuevo = st.text_input("PIN de 6 números", type="password", max_chars=6)
                        crear_cuenta = st.form_submit_button(
                            "Crear cuenta compartida",
                            type="primary",
                            use_container_width=True,
                        )
                    if crear_cuenta:
                        apodo_nuevo = (apodo_nuevo or "").strip()
                        pin_nuevo = pin_nuevo or ""
                        if not validar_apodo(apodo_nuevo):
                            st.warning("El apodo debe tener entre 3 y 24 letras, números, espacios, puntos o guiones.")
                        elif not pin_valido(pin_nuevo):
                            st.warning("El PIN debe tener exactamente 6 números.")
                        else:
                            try:
                                documento_id, perfil_registrado = registrar_alumna(
                                    DB_COMPARTIDA,
                                    apodo_nuevo,
                                    pin_nuevo,
                                )
                            except AlreadyExists:
                                st.error("Ese apodo ya existe. Elige otro o inicia sesión.")
                            except (FirebaseError, GoogleAPICallError) as error:
                                st.error(f"No se pudo crear la cuenta: {error}")
                            else:
                                cargar_perfil_en_sesion(
                                    apodo_nuevo,
                                    documento_id,
                                    perfil_registrado,
                                    compartido=True,
                                )
                                st.rerun()
                with ingreso_tab:
                    with st.form("form_ingreso_compartido"):
                        apodo_ingreso = st.text_input("Apodo", max_chars=24, key="login_apodo")
                        pin_ingreso = st.text_input(
                            "PIN de 6 números",
                            type="password",
                            max_chars=6,
                            key="login_pin",
                        )
                        iniciar_sesion = st.form_submit_button(
                            "Entrar",
                            type="primary",
                            use_container_width=True,
                        )
                    if iniciar_sesion:
                        apodo_ingreso = (apodo_ingreso or "").strip()
                        pin_ingreso = pin_ingreso or ""
                        if not validar_apodo(apodo_ingreso) or not pin_valido(pin_ingreso):
                            st.warning("Escribe tu apodo y un PIN de exactamente 6 números.")
                        else:
                            try:
                                autenticacion, error_login = autenticar_alumna(
                                    DB_COMPARTIDA,
                                    apodo_ingreso,
                                    pin_ingreso,
                                )
                            except (FirebaseError, GoogleAPICallError) as error:
                                st.error(f"No se pudo iniciar sesión: {error}")
                            else:
                                if autenticacion is None:
                                    st.error(error_login or "No se pudo validar la cuenta.")
                                else:
                                    documento_id, perfil = autenticacion
                                    cargar_perfil_en_sesion(
                                        perfil.get("apodo", apodo_ingreso),
                                        documento_id,
                                        perfil,
                                        compartido=True,
                                    )
                                    st.rerun()
    st.stop()

nav_brand, nav_home, nav_learn, nav_progress = st.columns(
    [2.5, 1, 1, 1],
    vertical_alignment="center",
)
with nav_brand:
    st.markdown(
        '<span class="brand-mark">🎭</span><span class="brand-title">Club de Teatro</span>',
        unsafe_allow_html=True,
    )

for columna, pagina, etiqueta in [
    (nav_home, "Inicio", "⌂  Inicio"),
    (nav_learn, "Aprender", "▣  Aprender"),
    (nav_progress, "Mi progreso", "♧  Mi progreso"),
]:
    with columna:
        if st.button(
            etiqueta,
            key=f"nav_{pagina}",
            type="primary" if st.session_state.pagina == pagina else "secondary",
            use_container_width=True,
        ):
            st.session_state.pagina = pagina
            st.rerun()

nombre_seguro = escape(st.session_state.nombre_alumna)
rango = obtener_rango(st.session_state.puntos)
rango_index = RANGOS.index(rango)
marco_actual = next(
    marco for marco in MARCOS if marco["nombre"] == st.session_state.marco_actual
)
if st.session_state.error_cuenta:
    st.warning(st.session_state.error_cuenta)

if st.session_state.pagina == "Inicio":
    with st.container(border=True):
        izquierda, avatar, derecha = st.columns([4, 1, 1.3], vertical_alignment="center")
        with izquierda:
            st.markdown(
                f"""
                <div class="welcome-card">
                  <div class="section-eyebrow">Tu tablero de aprendizaje</div>
                  <h1 style="margin:.3rem 0 0">¡Hola, {nombre_seguro}! 👋</h1>
                  <p>Hoy es un buen día para practicar, aprender y subir de nivel.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with avatar:
            st.image(
                crear_foto_con_marco(st.session_state.foto_perfil, marco_actual),
                width=110,
            )
        with derecha:
            st.markdown(f"### {rango['insignia']} {rango['nombre']}")
            st.caption(f"Marco {marco_actual['detalle']}")

    puntos_col, rango_col, saldo_col = st.columns(3)
    with puntos_col:
        st.metric("✨ Puntos ganados", st.session_state.puntos)
    with rango_col:
        st.metric("🏆 Tu rango", f"{rango['insignia']} {rango['nombre']}")
    with saldo_col:
        st.metric("🪙 Puntos para marcos", st.session_state.puntos_disponibles)

    izquierda, derecha = st.columns([1.25, 1], gap="large")
    with izquierda:
        with st.container(border=True):
            st.markdown('<div class="section-eyebrow">Tu camino</div>', unsafe_allow_html=True)
            if rango_index < len(RANGOS) - 1:
                siguiente = RANGOS[rango_index + 1]
                progreso = (st.session_state.puntos - rango["minimo"]) / (
                    siguiente["minimo"] - rango["minimo"]
                )
                st.markdown(f"### Próximo rango: {siguiente['insignia']} {siguiente['nombre']}")
                st.progress(max(0.0, min(progreso, 1.0)))
                st.write(f"Te faltan **{siguiente['minimo'] - st.session_state.puntos} puntos ganados**.")
            else:
                st.markdown("### ¡Rango máximo: Reina! 👑")
                st.progress(1.0)
            st.caption("Los rangos se basan en todos los puntos que ganas; comprar marcos no los reduce.")
    with derecha:
        with st.container(border=True):
            st.markdown('<div class="section-eyebrow">Listo para jugar</div>', unsafe_allow_html=True)
            st.markdown("### ¿Practicamos un poco? 🎬")
            st.write(f"Hay {len(QUESTIONS)} preguntas mezcladas y tres dificultades para elegir.")
            if st.button("Ir a Aprender ➜", type="primary", use_container_width=True):
                st.session_state.pagina = "Aprender"
                st.rerun()

elif st.session_state.pagina == "Aprender":
    st.markdown(f"## ¡A escena, {nombre_seguro}! 🎭")
    st.caption("El orden de las preguntas y de las cuatro opciones cambia en cada ronda.")

    if not st.session_state.quiz_activo and not st.session_state.quiz_terminado:
        with st.container(border=True):
            st.markdown('<div class="section-eyebrow">Preparar reto</div>', unsafe_allow_html=True)
            st.markdown("### Elige tu dificultad y empieza")
            dificultades = [*DIFICULTAD_INDICES, "Mixto"]
            dificultad = st.selectbox(
                "Dificultad",
                dificultades,
                index=dificultades.index(st.session_state.nivel_dificultad),
                format_func=lambda nivel: {
                    "Fácil": "🌱 Fácil · conceptos básicos",
                    "Normal": "🎭 Normal · comprensión y aplicación",
                    "Difícil": "🔥 Difícil · análisis teatral",
                    "Mixto": f"🎲 Mixto · las {len(QUESTIONS)} preguntas",
                }[nivel],
                key="selector_dificultad",
            )
            if dificultad == "Mixto":
                pool = list(QUESTIONS)
            else:
                pool = [
                    pregunta
                    for indice, pregunta in enumerate(QUESTIONS)
                    if indice in DIFICULTAD_INDICES[dificultad]
                ]
            cantidades = sorted({5, min(10, len(pool)), min(15, len(pool)), len(pool)})
            cantidad = st.selectbox(
                "Preguntas de esta ronda",
                cantidades,
                format_func=lambda cantidad: (
                    f"Toda la categoría ({cantidad})"
                    if cantidad == len(pool)
                    else str(cantidad)
                ),
            )
            st.caption("Cada acierto suma 1 punto ganado y 1 punto disponible para canjear marcos.")
            if st.button("Comenzar ronda 🎬", type="primary", use_container_width=True):
                ronda_aleatoria = sample(pool, cantidad)
                st.session_state.preguntas_ronda = mezclar_opciones(ronda_aleatoria)
                st.session_state.nivel_dificultad = dificultad
                st.session_state.quiz_activo = True
                st.session_state.quiz_terminado = False
                st.session_state.indice_pregunta = 0
                st.session_state.ronda += 1
                st.session_state.respuesta_revisada = False
                st.session_state.ultima_respuesta = None
                st.rerun()

    if st.session_state.quiz_activo and not st.session_state.quiz_terminado:
        indice = st.session_state.indice_pregunta
        total = len(st.session_state.preguntas_ronda)
        pregunta = st.session_state.preguntas_ronda[indice]
        with st.container(border=True):
            st.markdown(f"### Pregunta {indice + 1} de {total}")
            st.progress((indice + 1) / total)
            st.caption(
                f"{st.session_state.nivel_dificultad} · Ronda {st.session_state.ronda} "
                "· Cada respuesta correcta suma 1 punto"
            )
            st.subheader(pregunta["question"])
            if not st.session_state.respuesta_revisada:
                with st.form(f"form_pregunta_{st.session_state.ronda}_{indice}"):
                    respuesta = st.radio(
                        "Elige una respuesta:",
                        pregunta["options"],
                        index=None,
                        key=f"respuesta_{st.session_state.ronda}_{indice}",
                    )
                    revisar = st.form_submit_button(
                        "Comprobar respuesta ✨",
                        type="primary",
                        use_container_width=True,
                    )
                if revisar:
                    if respuesta is None:
                        st.warning("Elige una opción antes de comprobar.")
                    else:
                        st.session_state.ultima_respuesta = respuesta
                        st.session_state.respuesta_revisada = True
                        st.session_state.respuestas_respondidas += 1
                        if respuesta == pregunta["answer"]:
                            st.session_state.puntos += 1
                            st.session_state.puntos_disponibles += 1
                            st.session_state.respuestas_correctas += 1
                            rango_nuevo = obtener_rango(st.session_state.puntos)
                            if rango_nuevo["nombre"] != rango["nombre"]:
                                st.balloons()
                                st.toast(f"¡Nuevo rango: {rango_nuevo['nombre']}!", icon="🏆")
                        try:
                            guardar_perfil_remoto(DB_COMPARTIDA)
                            st.session_state.error_cuenta = ""
                        except (FirebaseError, GoogleAPICallError) as error:
                            st.session_state.error_cuenta = (
                                f"No se pudo sincronizar el progreso en línea: {error}"
                            )
                        st.rerun()
            else:
                if st.session_state.ultima_respuesta == pregunta["answer"]:
                    st.success(f"¡Muy bien, {st.session_state.nombre_alumna}! +1 punto ✨")
                else:
                    st.error(f"La respuesta correcta era: **{pregunta['answer']}**")
                st.info(pregunta["explanation"])
                if st.button(
                    "Ver la siguiente pregunta ➜",
                    type="primary",
                    use_container_width=True,
                ):
                    if indice + 1 == total:
                        st.session_state.quiz_terminado = True
                        st.session_state.quiz_activo = False
                    else:
                        st.session_state.indice_pregunta += 1
                    st.session_state.respuesta_revisada = False
                    st.session_state.ultima_respuesta = None
                    st.rerun()

    if st.session_state.quiz_terminado:
        st.balloons()
        st.markdown("### ¡Ronda completada! 🌟")
        st.write(
            f"¡Buen trabajo, {st.session_state.nombre_alumna}! "
            f"Tu rango es **{obtener_rango(st.session_state.puntos)['nombre']}**."
        )
        if st.button("Jugar otra ronda 🎭", type="primary"):
            st.session_state.quiz_terminado = False
            st.rerun()

elif st.session_state.pagina == "Mi progreso":
    st.markdown(f"## Perfil de {nombre_seguro} 🌷")
    foto_col, datos_col = st.columns([1, 2], gap="large")
    with foto_col:
        st.image(crear_foto_con_marco(st.session_state.foto_perfil, marco_actual), width=240)
        st.caption(f"Marco equipado: **{marco_actual['nombre']}**")
    with datos_col:
        with st.container(border=True):
            st.markdown("### Tu foto de perfil")
            foto_subida = st.file_uploader(
                "Elige una imagen",
                type=["png", "jpg", "jpeg", "webp"],
                help="La foto se mantiene en esta sesión; usa una imagen que tengas permiso para compartir.",
            )
            if foto_subida is not None:
                contenido_foto = foto_subida.getvalue()
                if len(contenido_foto) > 5 * 1024 * 1024:
                    st.error("La imagen supera el límite de 5 MB.")
                else:
                    try:
                        Image.open(BytesIO(contenido_foto)).verify()
                    except (OSError, ValueError):
                        st.error("No se pudo abrir esa imagen. Prueba con un JPG, PNG o WEBP válido.")
                    else:
                        st.session_state.foto_perfil = contenido_foto
                        st.success("Foto actualizada para esta sesión.")
        with st.container(border=True):
            st.markdown("### Cambiar apodo")
            with st.form("form_cambiar_apodo"):
                nuevo_apodo = st.text_input(
                    "Nuevo apodo",
                    value=st.session_state.nombre_alumna,
                    max_chars=24,
                    key="campo_nuevo_apodo",
                )
                guardar_apodo = st.form_submit_button("Guardar apodo")
            if guardar_apodo:
                nuevo_apodo = (nuevo_apodo or "").strip()
                if nuevo_apodo:
                    if not validar_apodo(nuevo_apodo):
                        st.warning("El apodo debe tener entre 3 y 24 caracteres.")
                    elif st.session_state.perfil_compartido:
                        try:
                            nuevo_id, cambiado = renombrar_alumna(
                                DB_COMPARTIDA,
                                st.session_state.usuario_id,
                                nuevo_apodo,
                            )
                        except (FirebaseError, GoogleAPICallError) as error:
                            st.error(f"No se pudo cambiar el apodo: {error}")
                        else:
                            if cambiado:
                                st.session_state.nombre_alumna = " ".join(nuevo_apodo.split())
                                st.session_state.usuario_id = nuevo_id
                                st.rerun()
                            else:
                                st.error("Ese apodo ya está en uso.")
                    else:
                        st.session_state.nombre_alumna = " ".join(nuevo_apodo.split())
                        st.rerun()
                else:
                    st.warning("El apodo no puede quedar vacío.")

    st.markdown("### Marcos de perfil")
    st.write(
        f"Saldo para canjear: **{st.session_state.puntos_disponibles} puntos** · "
        f"Los marcos se desbloquean al alcanzar su rango."
    )
    columnas_marcos = st.columns(4)
    for indice, marco in enumerate(MARCOS):
        with columnas_marcos[indice % 4]:
            with st.container(border=True):
                st.image(crear_foto_con_marco(st.session_state.foto_perfil, marco), width=175)
                st.markdown(
                    f'<div class="frame-label">{marco["nombre"]} · {marco["detalle"]}</div>',
                    unsafe_allow_html=True,
                )
                requerido = obtener_rango(marco["minimo"])
                st.caption(
                    f"Rango {requerido['nombre']} · "
                    f"{'Gratis' if marco['precio'] == 0 else f'{marco['precio']} puntos'}"
                )
                adquirido = marco["nombre"] in st.session_state.marcos_propios
                nivel_disponible = st.session_state.puntos >= marco["minimo"]
                if adquirido:
                    if st.session_state.marco_actual == marco["nombre"]:
                        st.button("Equipado ✓", key=f"marco_{indice}", disabled=True, use_container_width=True)
                    elif st.button("Equipar", key=f"marco_{indice}", use_container_width=True):
                        st.session_state.marco_actual = marco["nombre"]
                        try:
                            guardar_perfil_remoto(DB_COMPARTIDA)
                            st.session_state.error_cuenta = ""
                        except (FirebaseError, GoogleAPICallError) as error:
                            st.session_state.error_cuenta = (
                                f"El marco se equipó, pero no se pudo sincronizar: {error}"
                            )
                        st.rerun()
                elif not nivel_disponible:
                    st.button(
                        f"Desbloquea con {marco['minimo']} puntos",
                        key=f"marco_{indice}",
                        disabled=True,
                        use_container_width=True,
                    )
                elif st.session_state.puntos_disponibles < marco["precio"]:
                    st.button(
                        f"Faltan {marco['precio'] - st.session_state.puntos_disponibles} puntos",
                        key=f"marco_{indice}",
                        disabled=True,
                        use_container_width=True,
                    )
                elif st.button(
                    f"Canjear · {marco['precio']} pts",
                    key=f"marco_{indice}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.puntos_disponibles -= marco["precio"]
                    st.session_state.marcos_propios.append(marco["nombre"])
                    st.session_state.marco_actual = marco["nombre"]
                    try:
                        guardar_perfil_remoto(DB_COMPARTIDA)
                        st.session_state.error_cuenta = ""
                    except (FirebaseError, GoogleAPICallError) as error:
                        st.session_state.error_cuenta = (
                            f"El marco se canjeó, pero no se pudo sincronizar: {error}"
                        )
                    st.toast(f"¡Marco {marco['nombre']} canjeado y equipado!", icon="🖼️")
                    st.rerun()

    st.markdown("### Resumen de aprendizaje")
    resumen_a, resumen_b, resumen_c = st.columns(3)
    with resumen_a:
        st.metric("Puntos ganados", st.session_state.puntos)
    with resumen_b:
        st.metric("Respuestas correctas", st.session_state.respuestas_correctas)
    with resumen_c:
        precision = (
            st.session_state.respuestas_correctas / st.session_state.respuestas_respondidas * 100
            if st.session_state.respuestas_respondidas
            else 0
        )
        st.metric("Precisión", f"{precision:.0f}%")

    st.markdown("### Ranking del curso 🏅")
    if DB_COMPARTIDA is None:
        st.info(
            "El ranking aparecerá aquí cuando se conecte Firebase. "
            "Ahora los puntos solo se guardan en esta sesión."
        )
        if ERROR_FIRESTORE:
            st.error(f"No se pudo conectar con Firestore: {ERROR_FIRESTORE}")
        with st.expander("Activar ranking compartido"):
            st.markdown(
                """
                1. Crea un proyecto en [Firebase Console](https://console.firebase.google.com/).
                2. Activa **Cloud Firestore**.
                3. En Configuración del proyecto → Cuentas de servicio, genera una clave privada.
                4. Guarda esa clave localmente en `.streamlit/secrets.toml`; **no la envíes a nadie
                   ni la publiques en GitHub**.
                5. Al compartir la app en Streamlit Community Cloud, pega esos mismos valores en
                   **App settings → Secrets**. Las alumnas entrarán con apodo y PIN.
                """
            )
    else:
        try:
            ranking, alumnas_total, aciertos_del_curso = crear_ranking(DB_COMPARTIDA)
        except (FirebaseError, GoogleAPICallError) as error:
            st.error(f"No se pudo cargar el ranking compartido: {error}")
        else:
            st.caption("Se muestran solo apodos y puntos; no se publican PIN ni fotos.")
            if ranking:
                filas = [
                    {
                        "Posición": posicion,
                        "Apodo": apodo,
                        "Puntos": puntos,
                        "Rango": obtener_rango(puntos)["nombre"],
                    }
                    for posicion, (apodo, puntos) in enumerate(ranking, start=1)
                ]
                st.dataframe(filas, hide_index=True, use_container_width=True)
                st.markdown("#### Reto colectivo de la clase 🌟")
                meta_grupal = 500
                st.progress(min(aciertos_del_curso / meta_grupal, 1.0))
                st.write(
                    f"Entre **{alumnas_total}** artistas han conseguido "
                    f"**{aciertos_del_curso} de {meta_grupal} aciertos** para completar el reto."
                )
            else:
                st.info("Todavía no hay cuentas registradas. ¡Invita al grupo a unirse!")
