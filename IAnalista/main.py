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
    prompt_per_defecte = (
        "Cas de prova: Client amb Deute_Altres_Entitat:1000€, Lloguer:500€, "
        "1000€ de salari net, Contracte: Fixe, Quota_Prestec_Solicitat: 450€. "
        "Calcula el DTI com: (Deute_Altres_Entitat + Lloguer + Quota_Prestec_Solicitat) / salari_net * 100. "
        "Avalua solvència i DTI amb aquesta fórmula."
    )
    prompt = input(f"{prompt_per_defecte}: ").strip() or prompt_per_defecte

    # a la API de Gemini per obtenir resposta accedim com a client als seus models
    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                f"Ets un Analista de Risc de Préstecs. Analitza les dades del prompt i respon en JSON amb aquesta estructura exacta: "
                f"{'{'}'concedit': 'si/no', 'resposta': '2 línies de motiu', 'dti_percentatge': 'valor', 'nivell_risc': 'baix/mitjà/alt' {'}'}. "
                f"Calcula el DTI com: (Deute_Altres_Entitat + Lloguer + Quota_Prestec_Solicitat) / salari_net * 100."
                f"Ten en compte que la quota de préstec sol·licitada no pot superar el 35% del salari net, i que un DTI superior al 40% es considera alt risc."
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
