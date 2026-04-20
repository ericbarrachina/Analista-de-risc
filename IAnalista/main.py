import os, sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
CLAU = os.getenv("KEYAPI")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if CLAU is None:
    print("Alguna cosa no ha anat bé en el procés d'agafar la clau!!")
    sys.exit(1)

# creem un client per fer peticions amb l'APIKEY.
try:
    client = genai.Client(api_key=CLAU)

    # Si l'usuari prem ENTER sense text, fem servir un cas de prova neutre per defecte
    cliente_dades = {
        "deute_altres_entitat": 500,
        "lloguer": 1000,
        "salari_net": 3000,
        "contracte": "Fixe",
        "quota_prestec_solicitat": 200,
        "asnef": False
    }
    
    prompt_per_defecte = f"Analitza aquest client: {json.dumps(cliente_dades, ensure_ascii=False)}. Calcula el DTI = (deute_altres_entitat + lloguer + quota_prestec_solicitat) / salari_net * 100. Avalua solvència."
    prompt = input(f"{prompt_per_defecte}: ").strip() or prompt_per_defecte

    # a la API de Gemini per obtenir resposta accedim com a client als seus models
    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                f"Ets un Analista de Risc de Préstecs. Analitza les dades del prompt i respon en JSON amb aquesta estructura exacta: "
                f"{'{'}'concedit': 'si/no', 'resposta': '2 línies de motiu', 'dti_percentatge': 'valor', 'nivell_risc': 'baix/mitjà/alt', 'asnef': 'si/no' {'}'}. "
                f"Calcula el DTI com: (Deute_Altres_Entitat + Lloguer + Quota_Prestec_Solicitat) / salari_net * 100. "
                f"IMPORTANT - Verificació del 35%: Calcula el 35% del salari net. Si la Quota_Prestec_Solicitat és menor que aquest 35%, és acceptable. "
                f"Un DTI superior al 40% es considera alt risc. "
                f"ASNEF: Comprova si el client apareix a la llista ASNEF (bases de dades de morosos espanyola). Si és el cas, concedit='no'."
            ),
            temperature=0.0,
            top_p=1.0,
            top_k=1,
            max_output_tokens=1000,
            response_mime_type="application/json",
        ),
    )

    print(f"\n{5*'='} RESPOSTA JSON {5*'='}")

    # Intentem carregar el JSON per mostrar-lo bonic, si no, imprimim el text
    try:
        dades_json = json.loads(resposta.text)
        print(json.dumps(dades_json, indent=4, ensure_ascii=False))
    except:
        print(resposta.text)

    print(f"\nTokens gastats: {resposta.usage_metadata.total_token_count}")

except Exception as e:
    print(f"Error: {e}- No es genera resposta")
