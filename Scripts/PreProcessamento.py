import nltk
nltk.download('punkt')

from nltk.tokenize import sent_tokenize



def segmentar_em_frases_identificando_idioma(paragrafos_json):
    """
    Segmenta os textos de parágrafos em frases, identificando automaticamente o idioma com base no nome da coluna.

    Returns:
        lista de dicionários, cada um representando uma frase segmentada, com metadados.
    """
    frases_json = []

    for par in paragrafos_json:
        # Campos fixos
        base = {k: par[k] for k in par if k in ['source_book', 'paragraph_id', 'master_name', 'master_url']}
        
        for col, texto in par.items():
            if col in base or not isinstance(texto, str):
                continue

            col_lower = col.lower()
            if "illustration" in col_lower:
                continue  # ignora imagens

            # Identificação do idioma
            if "translation" in col_lower:
                lang = "en"
            elif "transcription" in col_lower or "transcribed" in col_lower:
                lang = "it"
            else:
                lang = "unknown"

            frases = sent_tokenize(texto)
            for i, frase in enumerate(frases):
                entrada = base.copy()
                entrada.update({
                    "sentence_id": i,
                    "lang": lang,
                    "field_name": col,
                    "text": frase
                })
                frases_json.append(entrada)

    return frases_json