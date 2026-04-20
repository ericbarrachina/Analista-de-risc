import os, sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
CLAU = os.getenv("KEYAPI")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


def dades_des_de_entrada(text: str, per_defecte: dict) -> dict:
    """Enter buit → per_defecte; JSON vàlid → dict; si el text conté un JSON incrustat, el prova."""
    t = text.strip()
    if not t:
        return per_defecte
    try:
        d = json.loads(t)
        return d if isinstance(d, dict) else per_defecte
    except json.JSONDecodeError:
        pass
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j > i:
        try:
            d = json.loads(t[i : j + 1])
            return d if isinstance(d, dict) else per_defecte
        except json.JSONDecodeError:
            pass
    return per_defecte


if CLAU is None:
    print("Alguna cosa no ha anat bé en el procés d'agafar la clau!!")
    sys.exit(1)

try:
    client = genai.Client(api_key=CLAU)

    # Cas per defecte amb marge clar sobre el 40%: DTI = (400+500+300)/2500*100 = 48% (quota 300 < 35% de 2500 = 875)
    cliente_dades = {
        "deute_altres_entitat": 400,
        "lloguer": 500,
        "salari_net": 2500,
        "contracte": "Fixe",
        "quota_prestec_solicitat": 300,
        "asnef": False,
    }

    avís = (
        "Enganxa les dades del client en JSON (mateixes claus que l'exemple), o prem Enter per l'exemple per defecte."
    )
    entrada = input(f"{avís}\n> ").strip()
    dades_client = dades_des_de_entrada(entrada, cliente_dades)

    # Només passem les dades + una frase mínima; tots els càlculs els fa el model
    prompt = json.dumps(dades_client, ensure_ascii=False)

    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "Ets un Analista de Risc de Préstecs. Rep un únic JSON amb dades del client. "
                "Tu has de calcular tot aritmèticament a partir d'aquestes dades (el programa no calcula res). "
                "Respon només en JSON amb les claus EN AQUEST ORDRE: "
                "{'concedit': 'si/no', 'resposta': '2 línies de motiu', 'dti_percentatge': 'valor', "
                "'nivell_risc': 'baix/mitjà/alt', 'asnef': 'si/no'}. "
                "Per al DTI usa exclusivament aquests camps numèrics del JSON: deute_altres_entitat, lloguer, "
                "quota_prestec_solicitat i salari_net. Ignora altres camps (p. ex. contracte) per al càlcul del DTI. "
                "Fórmula DTI (%): (deute_altres_entitat + lloguer + quota_prestec_solicitat) / salari_net * 100. "
                "Passos obligatoris abans d'escriure el JSON: (1) Suma mentalment o per passos els TRES conceptes "
                "del numerador i comprova que cap queda fora (inclou sempre el lloguer si ve al JSON). "
                "(2) Divideix entre salari_net i multiplica per 100. (3) Arrodoneix dti_percentatge a 2 decimals. "
                "Si salari_net és 0 o no numèric, posa dti_percentatge coherent i explica l'error a resposta. "
                "Classificació nivell_risc segons el DTI que has calculat: baix si DTI <= 30%, mitjà si 30% < DTI <= 40%, alt si DTI > 40%. "
                "El camp asnef ha de reflectir el booleà del JSON (true → 'si', false → 'no'). "
                "A resposta, primera línia: una frase breu amb el desglossament numèric usat (suma mensual i salari). "
                "Segona línia: motiu de la decisió en llenguatge natural. "
                "CRÍTIC — Regla de concessió (sense excepcions): si asnef és 'si', concedit HA DE ser 'no'. "
                "Si el DTI (nombre de dti_percentatge) és estrictament superior a 40, concedit HA DE ser 'no' (mai 'si'). "
                "Només pots concedit='si' si DTI <= 40 i asnef és 'no'. "
                "La quota nova sola ha de ser estrictament inferior al 35% del salari net per ser considerada assumible; "
                "això no substitueix la regla del DTI: si el DTI total és >40%, no concedeixis encara que la quota sigui <35%. "
                "Si el DTI <= 40%, asnef és 'no' i la quota és < 35% del salari, pots concedir='si' salvo altres motius explícits a resposta. "
                "Abans de respondre, comprova coherència interna: si dti_percentatge implica DTI > 40%, nivell_risc ha de ser 'alt' "
                "i concedit ha de ser 'no'. Si detectes contradicció entre camps, corregeix el JSON."
            ),
            temperature=0.0,
            top_p=1.0,
            top_k=1,
            max_output_tokens=1000,
            response_mime_type="application/json",
        ),
    )

    print(f"\n{5*'='} RESPOSTA JSON {5*'='}")

    try:
        dades_json = json.loads(resposta.text)
        print(json.dumps(dades_json, indent=4, ensure_ascii=False))
    except Exception:
        print(resposta.text)

    print(f"\nTokens gastats: {resposta.usage_metadata.total_token_count}")

except Exception as e:
    print(f"Error: {e}- No es genera resposta")
