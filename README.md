# Wordle senza limiti

Web app tipo Wordle sviluppata con [Streamlit](https://streamlit.io) che supporta parole di lunghezza arbitraria. La parola segreta è scelta da dizionari caricati manualmente e cambia ogni giorno nella modalità Daily basata sul fuso orario Europe/Rome.

## Requisiti

- Python 3.10 o superiore
- Dipendenze elencate in `requirements.txt`

Installa le dipendenze ed avvia l'applicazione con:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dizionari

La cartella `data/` è inclusa nel repository (vuota a parte da un segnaposto) per ospitare il dizionario delle risposte personalizzato:

- `data/answers.txt`: elenco delle possibili parole segrete, una per riga, senza limitazioni di lunghezza.

Se il file non esiste viene creato automaticamente con un esempio minimo e l'app mostra un avviso. Sostituiscilo con il tuo elenco (una parola per riga, niente spazi iniziali/finali). Non vengono normalizzati accenti o maiuscole/minuscole: le parole sono confrontate così come scritte nel file.

## Modalità di gioco

- **Daily**: tutti i giocatori ricevono la stessa parola del giorno. L'indice è calcolato sulla data locale Europe/Rome e cambia a mezzanotte.
- **Free play**: genera una nuova parola casuale ogni volta che premi "Nuova partita".

Nel pannello laterale puoi modificare il numero massimo di tentativi (default 6), attivare la modalità difficile (i tentativi successivi devono rispettare le lettere già confermate) e abilitare una palette ad alto contrasto per daltonici.

## Interfaccia

- Griglia dinamica che si adatta alla lunghezza della parola corrente.
- Tastiera virtuale mostrata automaticamente quando l'alfabeto dei dizionari è compatto (≤40 simboli stampabili).
- Campo di input senza limite di caratteri: la validazione assicura che ogni tentativo abbia la stessa lunghezza della soluzione e rispetti gli eventuali vincoli della modalità difficile.
- Pulsanti rapidi per inviare, cancellare o avviare una nuova partita e bottone di condivisione che copia negli appunti la griglia in formato emoji.

## Test

Esegui la suite automatica con:

```bash
pytest
```

I test coprono lo scoring delle parole, la gestione dei duplicati e la selezione della parola giornaliera.
