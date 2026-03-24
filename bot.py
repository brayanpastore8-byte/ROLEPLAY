import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import asyncio
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv("MTQ4NTkzODQzMTQwNTA2NDIyMg.GqBoXM.-JdmN26XYy-3XoBbqFtj2kKDIgMUc1etTfHlfU")
ID_CANALE_LOG = 1485941245179334777
ID_RUOLO_CITTADINO = 1485944410641403904

BANNER_URL = "https://i.imgur.com/placeholder.png"

# --- KEEP ALIVE SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- DATABASE ECONOMIA E INVENTARIO ---
con = sqlite3.connect("economy.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        wallet INTEGER DEFAULT 500,
        bank INTEGER DEFAULT 2000
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER PRIMARY KEY,
        pietra INTEGER DEFAULT 0,
        carbone INTEGER DEFAULT 0,
        ferro INTEGER DEFAULT 0,
        oro INTEGER DEFAULT 0,
        diamanti INTEGER DEFAULT 0
    )
""")
con.commit()

def get_balance(user_id):
    cur.execute("SELECT wallet, bank FROM users WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        con.commit()
        return (500, 2000)
    return res

def update_balance(user_id, wallet=None, bank=None):
    current = get_balance(user_id)
    new_wallet = wallet if wallet is not None else current[0]
    new_bank = bank if bank is not None else current[1]
    
    cur.execute("UPDATE users SET wallet = ?, bank = ? WHERE user_id = ?", (new_wallet, new_bank, user_id))
    con.commit()

def get_inventory(user_id):
    cur.execute("SELECT pietra, carbone, ferro, oro, diamanti FROM inventory WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO inventory (user_id) VALUES (?)", (user_id,))
        con.commit()
        return (0, 0, 0, 0, 0)
    return res

def update_inventory(user_id, pietra=0, carbone=0, ferro=0, oro=0, diamanti=0):
    current = get_inventory(user_id)
    cur.execute("""
        UPDATE inventory 
        SET pietra = ?, carbone = ?, ferro = ?, oro = ?, diamanti = ? 
        WHERE user_id = ?
    """, (
        current[0] + pietra,
        current[1] + carbone,
        current[2] + ferro,
        current[3] + oro,
        current[4] + diamanti,
        user_id
    ))
    con.commit()


# --- COMANDI CITTADINANZA ---
class RifiutaModal(discord.ui.Modal, title='Motivo Rifiuto'):
    motivo = discord.ui.TextInput(
        label='Scrivi qui la motivazione del rifiuto:',
        style=discord.TextStyle.paragraph,
        required=True
    )

    def __init__(self, target_user_id: int):
        super().__init__()
        self.target_user_id = target_user_id

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = guild.get_member(self.target_user_id)
        if not member:
            try:
                member = await guild.fetch_member(self.target_user_id)
            except Exception:
                pass
        
        if member:
            embed = discord.Embed(
                title="TECNO ROLEPLAY - Esito Cittadinanza",
                description=f"La tua richiesta di cittadinanza è stata **RIFIUTATA**.\n\n**Motivazione:**\n```\n{self.motivo.value}\n```\n*Rifiutata da:* {interaction.user.name}",
                color=discord.Color.red()
            )
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

        await interaction.response.edit_message(content=f"❌ Cittadinanza **RIFIUTATA** per <@{self.target_user_id}> da {interaction.user.mention}\n**Motivo:** {self.motivo.value}", view=None, embed=None)

class CittadinanzaModal(discord.ui.Modal, title='Richiesta Cittadinanza'):
    username_roblox = discord.ui.TextInput(
        label='Username Roblox', style=discord.TextStyle.short, required=True
    )
    nome_cognome = discord.ui.TextInput(
        label='Nome e Cognome', style=discord.TextStyle.short, required=True
    )
    data_nascita = discord.ui.TextInput(
        label='Data di Nascita (GG-MM-AAAA)', style=discord.TextStyle.short, required=True
    )
    genere = discord.ui.TextInput(
        label='Genere (UOMO/DONNA)', style=discord.TextStyle.short, required=True
    )
    nazionalita = discord.ui.TextInput(
        label='Nazionalità', style=discord.TextStyle.short, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user
        
        channel = interaction.guild.get_channel(ID_CANALE_LOG)
        if channel:
            embed = discord.Embed(
                title="TECNO ROLEPLAY - Richiesta Cittadinanza",
                color=0x2F3136
            )
            embed.add_field(name="Discord", value=user.mention, inline=False)
            embed.add_field(name="Username Roblox", value=self.username_roblox.value, inline=False)
            embed.add_field(name="Nome e Cognome", value=self.nome_cognome.value, inline=False)
            embed.add_field(name="Data di Nascita", value=self.data_nascita.value, inline=False)
            embed.add_field(name="Genere", value=self.genere.value, inline=False)
            embed.add_field(name="Nazionalità", value=self.nazionalita.value, inline=False)
            embed.set_footer(text=f"TECNO ROLEPLAY • ID: {user.id}")

            view = discord.ui.View(timeout=None)
            btn_accetta = discord.ui.Button(label="Accetta", style=discord.ButtonStyle.success, custom_id=f"accetta_{user.id}")
            btn_rifiuta = discord.ui.Button(label="Rifiuta", style=discord.ButtonStyle.danger, custom_id=f"rifiuta_{user.id}")
            view.add_item(btn_accetta)
            view.add_item(btn_rifiuta)
            
            await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message('La tua richiesta è stata mandata con successo!', ephemeral=True)


class RichiediView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Richiedi Cittadinanza", style=discord.ButtonStyle.primary, custom_id="btn_richiedi_main")
    async def richiedi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CittadinanzaModal())


# --- INTERFACCIA SCAMBIO MINERALI ---
class ScambiaQuantitaModal(discord.ui.Modal, title='Quantità da Scambiare'):
    quantita = discord.ui.TextInput(
        label='Quante unità vuoi inviare?',
        placeholder='Inserisci un numero (es: 5)',
        min_length=1,
        max_length=5
    )

    def __init__(self, minerale: str, target: discord.Member):
        super().__init__()
        self.minerale = minerale.lower()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qta = int(self.quantita.value)
        except ValueError:
            return await interaction.response.send_message("❌ Inserisci un numero valido.", ephemeral=True)
        
        if qta <= 0:
            return await interaction.response.send_message("❌ La quantità deve essere maggiore di zero.", ephemeral=True)

        # Controlla inventario del mittente
        inv = get_inventory(interaction.user.id)
        # Mapping indici: pietra=0, carbone=1, ferro=2, oro=3, diamanti=4
        mapping = {"pietra": 0, "carbone": 1, "ferro": 2, "oro": 3, "diamanti": 4}
        idx = mapping.get(self.minerale)
        if idx is None or inv[idx] < qta:
            # Se idx è None non dovrebbe succedere per via del Select, ma aggiungiamo il check di sicurezza
            limite = inv[idx] if idx is not None else 0
            return await interaction.response.send_message(f"❌ Non hai abbastanza `{self.minerale}`! Ne hai solo `{limite}`.", ephemeral=True)

        # Esegui lo scambio
        # Togli al mittente
        kwargs_remove = {self.minerale: -qta}
        update_inventory(interaction.user.id, **kwargs_remove)
        
        # Aggiungi al destinatario
        kwargs_add = {self.minerale: qta}
        update_inventory(self.target.id, **kwargs_add)

        embed = discord.Embed(
            title="📦 Scambio Completato",
            description=f"Hai inviato **{qta}x {self.minerale.capitalize()}** a {self.target.mention}.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="TECNO ROLEPLAY - Economia Mineraria")
        
        await interaction.response.edit_message(content=f"✅ Scambio con {self.target.mention} riuscito!", view=None, embed=embed)
        
        # Notifica il destinatario se possibile
        try:
            notifica = discord.Embed(
                title="📦 Hai ricevuto dei minerali!",
                description=f"{interaction.user.mention} ti ha inviato **{qta}x {self.minerale.capitalize()}**.",
                color=discord.Color.green()
            )
            await self.target.send(embed=notifica)
        except:
            pass

class ScambiaSelect(discord.ui.Select):
    def __init__(self, target: discord.Member, options_list):
        super().__init__(placeholder="Scegli il minerale da scambiare...", options=options_list)
        self.target = target

    async def callback(self, interaction: discord.Interaction):
        minerale_scelto = self.values[0]
        await interaction.response.send_modal(ScambiaQuantitaModal(minerale_scelto, self.target))

class ScambiaView(discord.ui.View):
    def __init__(self, target: discord.Member, options_list):
        super().__init__(timeout=60)
        self.add_item(ScambiaSelect(target, options_list))


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(RichiediView())
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and "custom_id" in interaction.data:
        custom_id = interaction.data["custom_id"]
        
        if custom_id.startswith("accetta_"):
            user_id = int(custom_id.split("_")[1])
            guild = interaction.guild
            member = guild.get_member(user_id)
            if not member:
                try:
                    member = await guild.fetch_member(user_id)
                except Exception:
                    pass
            
            if member:
                role = guild.get_role(ID_RUOLO_CITTADINO)
                if role:
                    await member.add_roles(role)
                
                embed = discord.Embed(
                    title="TECNO ROLEPLAY - Esito Cittadinanza",
                    description="La tua richiesta di cittadinanza è stata **ACCETTATA**.",
                    color=discord.Color.green()
                )
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass

            await interaction.response.edit_message(content=f"✅ Cittadinanza **ACCETTATA** per <@{user_id}> da {interaction.user.mention}", view=None, embed=None)

        elif custom_id.startswith("rifiuta_"):
            user_id = int(custom_id.split("_")[1])
            await interaction.response.send_modal(RifiutaModal(user_id))

@bot.event
async def on_ready():
    print(f'Bot online come {bot.user}')


@bot.tree.command(name="setup_cittadinanza", description="Invia il modulo per richiedere la cittadinanza")
@app_commands.default_permissions(administrator=True)
async def setup_cittadinanza(interaction: discord.Interaction):
    embed = discord.Embed(
        title='RICHIESTA CITTADINANZA — TECNO ROLEPLAY',
        description='Vuoi far parte della comunita di **TECNO ROLEPLAY**?\n\nClicca il pulsante qui sotto per compilare la richiesta di cittadinanza. Lo staff la esaminerà e riceverai una notifica in DM con l\'esito.\n\n**Requisiti:**\n*Avere un account Roblox attivo*\n*Rispettare le regole del server*\n*Compilare tutti i campi richiesti*',
        color=0x2F3136
    )
    if BANNER_URL != "https://i.imgur.com/placeholder.png":
        embed.set_image(url=BANNER_URL)
    embed.set_footer(text='TECNO ROLEPLAY®')

    view = RichiediView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message('Modulo di richiesta inviato con successo nel canale!', ephemeral=True)

# --- ECONOMIA ---
@bot.tree.command(name="mina", description="Vai in miniera a cercare minerali preziosi.")
@app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id) # 3 minuti di attesa
async def mina(interaction: discord.Interaction):
    await interaction.response.send_message("⛏️ **Picconando la dura roccia...**\n`[⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%`")
    
    await asyncio.sleep(1.5)
    await interaction.edit_original_response(content="⛏️ **Picconando la dura roccia...**\n`[🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜] 30%`")
    
    await asyncio.sleep(1.5)
    await interaction.edit_original_response(content="⛏️ **Picconando la dura roccia...**\n`[🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜] 60%`")
    
    await asyncio.sleep(1.5)
    await interaction.edit_original_response(content="⛏️ **Spostando i detriti...**\n`[🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜] 80%`")
    
    await asyncio.sleep(1.5)

    trovato = []
    
    if random.random() < 0.80:
        qta = random.randint(1, 5)
        update_inventory(interaction.user.id, pietra=qta)
        trovato.append(f"🪨 `{qta}x` Pietra")
        
    if random.random() < 0.60:
        qta = random.randint(1, 3)
        update_inventory(interaction.user.id, carbone=qta)
        trovato.append(f"⚫ `{qta}x` Carbone")
        
    if random.random() < 0.40:
        qta = random.randint(1, 2)
        update_inventory(interaction.user.id, ferro=qta)
        trovato.append(f"⛏️ `{qta}x` Ferro")
        
    if random.random() < 0.15:
        qta = 1
        update_inventory(interaction.user.id, oro=qta)
        trovato.append(f"🪙 `{qta}x` Oro")
        
    if random.random() < 0.05:
        qta = 1
        update_inventory(interaction.user.id, diamanti=qta)
        trovato.append(f"💎 `{qta}x` Diamante")
        
    if not trovato:
        messaggio = "Hai scavato a lungo ma non hai trovato niente di utile questa volta."
        color = 0x95a5a6
    else:
        messaggio = "Hai scavato nella roccia e hai raccolto:\n" + "\n".join(trovato)
        color = 0x3498db
        
    embed = discord.Embed(
        title="⛏️ Sistema di Minaggio",
        description=messaggio,
        color=color
    )
    await interaction.edit_original_response(content="⛏️ **Scavo Completato!**\n`[🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100%`", embed=embed)

@mina.error
async def mina_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        minuti = int(error.retry_after // 60)
        secondi = int(error.retry_after % 60)
        await interaction.response.send_message(f"⏳ Il tuo piccone è rovinato! Riposati e riprova tra `{minuti}m e {secondi}s`.", ephemeral=True)

@bot.tree.command(name="inventario", description="Controlla lo zaino e i minerali che hai raccolto.")
async def inventario(interaction: discord.Interaction):
    inv = get_inventory(interaction.user.id)
    
    embed = discord.Embed(
        title="🎒 Inventario Minerario",
        description=f"**Minatore:** {interaction.user.mention}\nEcco i materiali che hai nello zaino pronti da vendere:",
        color=0x9b59b6
    )
    embed.add_field(name="🪨 Pietra", value=f"`{inv[0]}` unità", inline=True)
    embed.add_field(name="⚫ Carbone", value=f"`{inv[1]}` unità", inline=True)
    embed.add_field(name="⛏️ Ferro", value=f"`{inv[2]}` unità", inline=True)
    embed.add_field(name="🪙 Oro", value=f"`{inv[3]}` unità", inline=True)
    embed.add_field(name="💎 Diamanti", value=f"`{inv[4]}` unità", inline=True)
    
    embed.set_footer(text="Usa /vendi_minerali presso il compratore cittadino.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vendi_minerali", description="Vendi al banco dei pegni tutto l'inventario minerario in blocco.")
async def vendi_minerali(interaction: discord.Interaction):
    inv = get_inventory(interaction.user.id)
    pietra, carbone, ferro, oro, diamanti = inv
    
    if all(x == 0 for x in inv):
        return await interaction.response.send_message("❌ Il tuo inventario è **vuoto**. Usa prima `/mina` per raccogliere materiali!", ephemeral=True)
        
    # Prezzi in RP (Dollari)
    valore = 0
    valore += pietra * 2
    valore += carbone * 5
    valore += ferro * 15
    valore += oro * 50
    valore += diamanti * 200
    
    # Svuota l'inventario azzerando i valori
    cur.execute("UPDATE inventory SET pietra=0, carbone=0, ferro=0, oro=0, diamanti=0 WHERE user_id = ?", (interaction.user.id,))
    con.commit()
    
    # Dai i soldi
    wallet, bank = get_balance(interaction.user.id)
    update_balance(interaction.user.id, wallet=wallet + valore)
    
    embed = discord.Embed(
        title="💰 Vendita Minerali Completata",
        description=f"Hai venduto tutto il carico minerario al compratore cittadino.\n\n**Ricavo Totale:** `${valore:,}` in contanti aggiunti al tuo portafoglio.",
        color=0x2ecc71
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="scambia_minerale", description="Scambia minerali con un altro cittadino.")
@app_commands.describe(utente="Il cittadino a cui vuoi inviare i minerali")
async def scambia(interaction: discord.Interaction, utente: discord.Member):
    if utente.bot or utente.id == interaction.user.id:
        return await interaction.response.send_message("❌ Non puoi scambiare minerali con te stesso o con un bot.", ephemeral=True)
    
    inv = get_inventory(interaction.user.id)
    pietra, carbone, ferro, oro, diamanti = inv
    
    options = []
    if pietra > 0: options.append(discord.SelectOption(label="Pietra", emoji="🪨", value="pietra", description=f"Ne hai {pietra}"))
    if carbone > 0: options.append(discord.SelectOption(label="Carbone", emoji="⚫", value="carbone", description=f"Ne hai {carbone}"))
    if ferro > 0: options.append(discord.SelectOption(label="Ferro", emoji="⛏️", value="ferro", description=f"Ne hai {ferro}"))
    if oro > 0: options.append(discord.SelectOption(label="Oro", emoji="🪙", value="oro", description=f"Ne hai {oro}"))
    if diamanti > 0: options.append(discord.SelectOption(label="Diamanti", emoji="💎", value="diamanti", description=f"Ne hai {diamanti}"))
    
    if not options:
        return await interaction.response.send_message("❌ Non hai minerali nel tuo inventario da scambiare!", ephemeral=True)
        
    view = ScambiaView(utente, options)
    await interaction.response.send_message(f"Seleziona quale minerale vuoi inviare a {utente.mention}:", view=view, ephemeral=True)

if __name__ == "__main__":
    keep_alive() # Avvia il server web per non far dormire Render
    bot.run(TOKEN)
