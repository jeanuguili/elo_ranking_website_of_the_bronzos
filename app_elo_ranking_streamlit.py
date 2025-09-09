import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# ----------------------------
# Liste des profils OP.GG
# ----------------------------
PLAYERS = {
    "RoidDesBronzes-EUW": "https://www.op.gg/summoners/euw/RoidDesBronzes-EUW",
    "Buldoshield-1123": "https://www.op.gg/summoners/euw/Buldoshield-1123",
    "Errewyn-K C": "https://www.op.gg/summoners/euw/Errewyn-K%20C"
}

# ----------------------------
# Fonction pour récupérer le meta
# ----------------------------
def get_rank_from_opgg(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    meta = soup.find("meta", {"name": "description"})
    if not meta:
        return {"summoner": url, "tier": "Unranked", "lp": "-", "wins": "-", "losses": "-", "url": url}

    content = meta["content"]

    # Si le joueur n'a pas de ranked
    if "Lv." in content:
        return {"summoner": content.split(" / ")[0], "tier": "Unranked", "lp": "-", "wins": "-", "losses": "-", "url": url}

    # Exemple de contenu : "RoidDesBronzes#EUW / Bronze 2 82LP / 17Victoire 10Défaite % de victoire 63%"
    summoner = content.split(" / ")[0]
    tier_lp = content.split(" / ")[1] if " / " in content else ""
    match = re.search(r"(\d+)Win (\d+)Lose", content)

    tier = " ".join(tier_lp.split()[:2])  # ex: "Bronze 2"
    lp = tier_lp.split()[-1] if "LP" in tier_lp else "0 LP"

    wins, losses = "-", "-"
    if match:
        wins, losses = match.groups()

    return {
        "summoner": summoner,
        "tier": tier,
        "lp": lp,
        "wins": wins,
        "losses": losses,
        "url": url
    }

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Classement LoL entre potes", page_icon="🎮", layout="centered")
st.title("🏆 Classement Elo LoL (via OP.GG)")

data = [get_rank_from_opgg(url) for url in PLAYERS.values()]
df = pd.DataFrame(data)

# ----------------------------
# Classement automatique avec sous-tiers
# ----------------------------
tier_order = {
    "IRON": 0,
    "BRONZE": 4,
    "SILVER": 8,
    "GOLD": 12,
    "PLATINUM": 16,
    "EMERALD": 20,
    "DIAMOND": 24,
    "MASTER": 28,
    "GRANDMASTER": 32,
    "CHALLENGER": 36
}

def score(row):
    if row["tier"] == "Unranked":
        return -1

    parts = row["tier"].split()  # ex: ["Bronze", "2"]
    tier_name = parts[0].upper()
    sub_tier = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 4

    # Sous-tier inversé : 1 = top, 4 = bas
    sub_tier_score = 4 - sub_tier

    # Calcul du score
    base = tier_order.get(tier_name, 0)
    lp = int(row["lp"].replace("LP","")) if "LP" in row["lp"] else 0

    return base + sub_tier_score + lp / 100  # LP ajoute un petit plus pour départager

df["Score"] = df.apply(score, axis=1)
df = df.sort_values("Score", ascending=False)

# ----------------------------
# Affichage
# ----------------------------
#st.dataframe(df[["summoner", "tier", "lp", "wins", "losses"]], use_container_width=True)
# ----------------------------
# Affichage custom
# ----------------------------
medals = ["🥇", "🥈", "🥉"]
colors = ["#FFD700", "#C0C0C0", "#CD7F32"]  # or, argent, bronze

st.subheader("Classement actuel")

for i, row in enumerate(df.to_dict(orient="records")):
    medal = medals[i] if i < 3 else "🎮"
    color = colors[i] if i < 3 else "#444444"

    with st.container():
        st.markdown(
            f"""
            <div style="background-color:{color};padding:15px;border-radius:10px;margin:10px 0;">
                <h3 style="margin:0;">
                    {medal} {row['summoner']}
                    <a href="{row['url']}" target="_blank" style="font-size:12px; color:#000; text-decoration:none; margin-left:8px;">
                        (op.gg)
                    </a>
                </h3>
                <p style="margin:0;">
                    <b>{row['tier']}</b> {row['lp']}  
                    | {row['wins']}W / {row['losses']}L
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )