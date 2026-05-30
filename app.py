import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'chiave_segreta'

# Configurazione del database e della chiave segreta per i messaggi flash
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)

# ==========================================
# MODELLI DEL DATABASE (Mappatura tabelle)
# ==========================================

class Categoria(db.Model):
    __tablename__ = 'categorie'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    
    # Relazione 1-a-molti: permette di accedere a tutte le ricette di una categoria
    ricette = db.relationship('Ricetta', backref='categoria', lazy=True)

class Ricetta(db.Model):
    __tablename__ = 'ricette'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    tempo_preparazione = db.Column(db.Integer, nullable=False)
    difficolta = db.Column(db.String(20), nullable=False)
    ingredienti = db.Column(db.Text, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorie.id', ondelete='SET NULL'))
    immagine_url = db.Column(db.String(500), nullable=True)
    data_creazione = db.Column(db.DateTime, default=db.func.current_timestamp())

# ==========================================
# ROTTE / LOGICA DELL'APPLICAZIONE
# ==========================================

# Rotta principale: mostra l'elenco delle ricette con filtri e ricerca (Punto 4 della consegna)
@app.route('/')
def index():
    # Recuperiamo i filtri dalla barra degli indirizzi (es. /?q=pasta&categoria=2)
    search_query = request.args.get('q', '')
    categoria_id = request.args.get('categoria', '')
    
    # Costruiamo la query di base sul database
    query = Ricetta.query
    
    # 1. Filtro di ricerca per titolo (case-insensitive)
    if search_query:
        query = query.filter(Ricetta.titolo.ilike(f"%{search_query}%"))
        
    # 2. Filtro per categoria
    if categoria_id:
        query = query.filter(Ricetta.categoria_id == int(categoria_id))
        
    # Ordiniamo le ricette dalle più recenti alle più vecchie
    ricette = query.order_by(Ricetta.data_creazione.desc()).all()
    
    # Recuperiamo anche tutte le categorie per popolare il menu a tendina dei filtri
    categorie = Categoria.query.all()
    
    return render_template('index.html', ricette=ricette, categorie=categorie, search_query=search_query, categoria_id=categoria_id)

# Rotta per aggiungere una nuova ricetta
@app.route('/aggiungi', methods=['GET', 'POST'])
def aggiungi():
    # Se l'utente ha premuto il tasto "Salva" nel form
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        descrizione = request.form.get('descrizione')
        tempo_preparazione = request.form.get('tempo_preparazione')
        difficolta = request.form.get('difficolta')
        ingredienti = request.form.get('ingredienti')
        categoria_id = request.form.get('categoria_id')
        immagine_url = request.form.get('immagine_url')

        # VALIDAZIONE DATI (Punto 4 della consegna)
        if not titolo or int(tempo_preparazione) <= 0:
            flash('Errore: Titolo mancante o tempo di preparazione non valido.', 'danger')
            return redirect(url_for('aggiungi'))

        # Creazione del nuovo record e salvataggio nel database
        nuova_ricetta = Ricetta(
            titolo=titolo,
            descrizione=descrizione,
            tempo_preparazione=int(tempo_preparazione),
            difficolta=difficolta,
            ingredienti=ingredienti,
            categoria_id=int(categoria_id),
            immagine_url=immagine_url
        )
        
        db.session.add(nuova_ricetta)
        db.session.commit()
        
        flash('Ricetta aggiunta con successo!', 'success')
        return redirect(url_for('index'))

    # Se l'utente sta solo visitando la pagina, mostriamo il form vuoto
    categorie = Categoria.query.all()
    return render_template('form.html', categorie=categorie)

# Rotta per visualizzare i dettagli di una singola ricetta
@app.route('/ricetta/<int:id>')
def dettaglio(id):
    # Cerca la ricetta per ID, se non esiste dà errore 404
    ricetta = Ricetta.query.get_or_404(id)
    return render_template('dettaglio.html', ricetta=ricetta)

# Rotta per eliminare una ricetta
@app.route('/elimina/<int:id>', methods=['POST'])
def elimina(id):
    ricetta = Ricetta.query.get_or_404(id)
    db.session.delete(ricetta)
    db.session.commit()
    flash('Ricetta eliminata con successo!', 'success')
    return redirect(url_for('index'))

# Rotta per modificare una ricetta esistente
@app.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica(id):
    # Recuperiamo la ricetta da modificare e tutte le categorie
    ricetta = Ricetta.query.get_or_404(id)
    categorie = Categoria.query.all()

    # Se l'utente ha premuto "Salva Modifiche"
    if request.method == 'POST':
        ricetta.titolo = request.form.get('titolo')
        ricetta.descrizione = request.form.get('descrizione')
        ricetta.tempo_preparazione = request.form.get('tempo_preparazione')
        ricetta.difficolta = request.form.get('difficolta')
        ricetta.ingredienti = request.form.get('ingredienti')
        ricetta.categoria_id = request.form.get('categoria_id')
        ricetta.immagine_url = request.form.get('immagine_url')

        # Validazione base
        if not ricetta.titolo or int(ricetta.tempo_preparazione) <= 0:
            flash('Errore: Titolo mancante o tempo non valido.', 'danger')
            return redirect(url_for('modifica', id=ricetta.id))

        # Salviamo le modifiche nel database (non serve db.session.add perché il record esiste già)
        db.session.commit()
        
        flash('Ricetta aggiornata con successo!', 'success')
        return redirect(url_for('dettaglio', id=ricetta.id))

    # Se visita la pagina, mostriamo il form precompilato
    return render_template('modifica.html', ricetta=ricetta, categorie=categorie)

if __name__ == '__main__':
    app.run(debug=True)