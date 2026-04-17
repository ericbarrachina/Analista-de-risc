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
    client=genai.Client(api_key=CLAU)

    # Mantenim l'input tal qual el tenies, l'usuari només ha de prémer ENTER o escriure
    prompt=input("No te rai/ASNEF, Deute_Altres_Entitat:200€,Lloger:400€,1500€ de salari net,Contracte: Indefinit, Quota_Prestec_Solicitat: 300€. Avalua solvència i DTI: ")

    # a la API de Gemini per obtenir resposta accedim com a client als seus models
    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                f"Ets un Analista de Risc de Préstecs. Respon sempre en JSON amb aquesta estructura exacta: "
                f"{'{'}'concedit': 'si/no', 'resposta': '2 línies de motiu', 'dti_percentatge': 'valor', 'nivell_risc': 'baix/mitjà/alt' {'}'}."
            ),
            temperature=0.2,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1000,
            response_mime_type="application/json"
        )
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