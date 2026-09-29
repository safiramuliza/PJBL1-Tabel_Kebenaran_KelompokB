import itertools
import re
import html as htmllib
import streamlit as st

# =========================================================
# 1. CORE LOGIC: TOKENIZER, PARSER, EVALUATOR
# =========================================================
# Prioritas operator (tertinggi -> terendah):
#   ~  >  &  >  |  >  ->  >  <->

MAX_VARS = 10

SYMBOL_MAP = {
    "¬": "~", "!": "~",
    "∧": "&", "∨": "|",
    "→": "->", "=>": "->",
    "↔": "<->", "<=>": "<->",
}

TOKEN_RE = re.compile(
    r"\s*(<->|<=>|->|=>|↔|→|∧|∨|¬|\^|[~!&|()]|[A-Za-z][A-Za-z0-9_]*)"
)


def normalize_expression(expr: str) -> str:
    """
    Menyamakan berbagai bentuk penulisan operator logika
    sebelum proses tokenisasi.

    AND : &, ^, ∧, AND
    OR  : |, ∨, OR
    NOT : ~, ¬, !, NOT
    IMP : ->, →, =>
    IFF : <->, ↔, <=>
    """
    expr = expr.strip()

    # Operator simbol
    expr = expr.replace("^", "&")
    expr = expr.replace("∧", "&")
    expr = expr.replace("∨", "|")
    expr = expr.replace("¬", "~")
    expr = expr.replace("!", "~")
    expr = expr.replace("→", "->")
    expr = expr.replace("↔", "<->")
    expr = expr.replace("=>", "->")
    expr = expr.replace("<=>", "<->")

    # Operator berbentuk kata
    expr = re.sub(r"\bAND\b", "&", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bOR\b", "|", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bNOT\b", "~", expr, flags=re.IGNORECASE)

    return expr


def tokenize(expr: str) -> list:
    tokens = []
    pos = 0
    expr = normalize_expression(expr)
    while pos < len(expr):
        m = TOKEN_RE.match(expr, pos)
        if not m:
            raise ValueError(f"Karakter tidak dikenali di dekat: '{expr[pos:pos + 5]}'")
        tok = m.group(1)
        tokens.append(SYMBOL_MAP.get(tok, tok))
        pos = m.end()
    if not tokens:
        raise ValueError("Ekspresi kosong.")
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def eat(self, expected=None):
        tok = self.peek()
        if tok is None:
            raise ValueError("Ekspresi berakhir terlalu cepat (ada operator/kurung yang belum lengkap).")
        if expected and tok != expected:
            raise ValueError(f"Diharapkan '{expected}' tetapi menemukan '{tok}'.")
        self.i += 1
        return tok

    def parse(self):
        node = self.parse_iff()
        if self.peek() is not None:
            raise ValueError(f"Token tidak terduga: '{self.peek()}'. Periksa kurung atau operator.")
        return node

    def parse_iff(self):
        node = self.parse_imp()
        while self.peek() == "<->":
            self.eat()
            node = ("iff", node, self.parse_imp())
        return node

    def parse_imp(self):
        node = self.parse_or()
        if self.peek() == "->":
            self.eat()
            node = ("imp", node, self.parse_imp())  # asosiatif kanan
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == "|":
            self.eat()
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.peek() == "&":
            self.eat()
            node = ("and", node, self.parse_not())
        return node

    def parse_not(self):
        if self.peek() == "~":
            self.eat()
            return ("not", self.parse_not())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok == "(":
            self.eat("(")
            node = self.parse_iff()
            self.eat(")")
            return node
        if tok is not None and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", tok):
            self.eat()
            return ("var", tok)
        raise ValueError(f"Diharapkan variabel atau '(' tetapi menemukan '{tok}'.")


def parse_expression(expr: str):
    return Parser(tokenize(expr)).parse()


def evaluate(node, env: dict) -> bool:
    kind = node[0]
    if kind == "var":
        return env[node[1]]
    if kind == "not":
        return not evaluate(node[1], env)
    a = evaluate(node[1], env)
    b = evaluate(node[2], env)
    if kind == "and":
        return a and b
    if kind == "or":
        return a or b
    if kind == "imp":
        return (not a) or b
    if kind == "iff":
        return a == b
    raise ValueError("Node tidak dikenal.")


def collect_vars(node, acc=None) -> set:
    if acc is None:
        acc = set()
    if node[0] == "var":
        acc.add(node[1])
    else:
        for child in node[1:]:
            collect_vars(child, acc)
    return acc


def generate_truth_table(expr: str):
    """Tabel kebenaran satu ekspresi. Return (variabel, rows, results)."""
    tree = parse_expression(expr)
    variables = sorted(collect_vars(tree))

    if not variables:
        return [], [], []
    if len(variables) > MAX_VARS:
        raise ValueError(f"Terlalu banyak variabel ({len(variables)}). Maksimal {MAX_VARS}.")

    rows, results = [], []
    for combo in itertools.product([True, False], repeat=len(variables)):
        env = dict(zip(variables, combo))
        res = evaluate(tree, env)
        results.append(res)

        row = {v: ("B" if val else "S") for v, val in env.items()}
        row["Hasil Evaluasi"] = "B" if res else "S"
        rows.append(row)

    return variables, rows, results


def check_argument(premises: list, conclusion: str):
    """
    Verifikasi argumen: valid jika (P1 & P2 & ...) -> K adalah tautologi.
    Return (variabel, rows, results, counterexamples).
    """
    prem_trees = [parse_expression(p) for p in premises]
    concl_tree = parse_expression(conclusion)

    all_vars = set()
    for t in prem_trees + [concl_tree]:
        collect_vars(t, all_vars)
    variables = sorted(all_vars)

    if not variables:
        raise ValueError("Variabel tidak ditemukan.")
    if len(variables) > MAX_VARS:
        raise ValueError(f"Terlalu banyak variabel ({len(variables)}). Maksimal {MAX_VARS}.")

    rows, results, counter = [], [], []
    for combo in itertools.product([True, False], repeat=len(variables)):
        env = dict(zip(variables, combo))
        prem_vals = [evaluate(t, env) for t in prem_trees]
        concl_val = evaluate(concl_tree, env)
        res = (not all(prem_vals)) or concl_val  # (P1 & P2 & ...) -> K
        results.append(res)

        row = {v: ("B" if val else "S") for v, val in env.items()}
        for idx, pv in enumerate(prem_vals, start=1):
            row[f"Premis {idx}"] = "B" if pv else "S"
        row["Konklusi"] = "B" if concl_val else "S"
        row["Hasil Evaluasi"] = "B" if res else "S"
        rows.append(row)

        if not res:
            counter.append(row)

    return variables, rows, results, counter


def classify_expression(results: list) -> str:
    if all(results):
        return "Tautologi (Selalu Benar)"
    elif not any(results):
        return "Kontradiksi (Selalu Salah)"
    else:
        return "Kontingensi (Bercampur Benar & Salah)"


# =========================================================
# 2. HELPER TAMPILAN
# =========================================================

def md(html: str):
    """Render HTML tanpa indentasi/baris kosong agar tidak dibaca sebagai blok kode Markdown."""
    clean = "\n".join(line.strip() for line in html.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


def render_custom_table(rows, highlight_rows=False):
    """Tabel kebenaran: B = teal, S = merah bata, kolom hasil diberi penekanan."""
    if not rows:
        return

    headers = list(rows[0].keys())
    result_key = "Hasil Evaluasi"

    html = '<div class="tt-wrap"><table class="tt"><thead><tr>'
    for h in headers:
        cls = ' class="tt-result"' if h == result_key else ""
        html += f"<th{cls}>{htmllib.escape(h)}</th>"
    html += "</tr></thead><tbody>"

    for row in rows:
        row_cls = ' class="tt-bad"' if highlight_rows and row[result_key] == "S" else ""
        html += f"<tr{row_cls}>"
        for h in headers:
            v = row[h]
            cls = "tt-result" if h == result_key else ""
            pill = "b" if v == "B" else "s"
            html += f'<td class="{cls}"><span class="pill pill-{pill}">{v}</span></td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    md(html)


def classification_style(status: str) -> str:
    if status.startswith("Tautologi"):
        return "tone-true"
    if status.startswith("Kontradiksi"):
        return "tone-false"
    return "tone-mixed"


def format_counterexample(row: dict, variables: list) -> str:
    parts = [f"{v} = {'B' if row[v] == 'B' else 'S'}" for v in variables]
    return ", ".join(parts)


# =========================================================
# 3. PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Simulator Logika",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# 4. CSS
# =========================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
    --paper: #F1F5F2;
    --surface: #FFFFFF;
    --ink: #12302B;
    --ink-soft: #4B635E;
    --line: #D3DED8;
    --teal: #0F766E;
    --teal-tint: #D7EFEA;
    --teal-deep: #0B5A54;
    --brick: #B4442B;
    --brick-tint: #F8DDD6;
    --amber: #E9B44C;
    --amber-tint: #FBEFD0;
}

/* ---------- Dasar ---------- */
.stApp {
    background: var(--paper);
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--ink);
}
.stApp p, .stApp li, .stApp label, .stApp span { color: inherit; }
.block-container { padding-top: 2rem; max-width: 1100px; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }

.stApp h1, .stApp h2, .stApp h3 {
    font-family: 'Bricolage Grotesque', sans-serif;
    color: var(--ink);
    letter-spacing: -0.01em;
}

/* ---------- Header ---------- */
.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 28px;
    flex-wrap: wrap;
    background-color: var(--ink);
    background-image:
        linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
    background-size: 28px 28px;
    border-radius: 14px;
    padding: 32px 36px;
    margin-bottom: 26px;
}
.hero h1 {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 38px;
    line-height: 1.1;
    color: #F1F5F2 !important;
    margin: 0 0 10px 0;
    padding: 0;
}
.hero p {
    color: #A9C2BB !important;
    font-size: 16px;
    margin: 0;
    max-width: 420px;
    line-height: 1.55;
}
.hero-mini {
    border-collapse: collapse;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
}
.hero-mini th {
    color: var(--amber) !important;
    font-weight: 600;
    padding: 6px 16px;
    border-bottom: 2px solid var(--amber);
    text-align: center;
}
.hero-mini td {
    padding: 6px 16px;
    text-align: center;
    color: #F1F5F2 !important;
    border-bottom: 1px solid rgba(255,255,255,0.12);
}
.hero-mini td.hb { color: #5FD3C6 !important; }
.hero-mini td.hs { color: #F09A86 !important; }

/* ---------- Panel ---------- */
.panel {
    background: var(--surface);
    border: 1px solid var(--line);
    border-left: 5px solid var(--teal);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 18px;
}
.panel h2 {
    font-size: 22px;
    font-weight: 800;
    margin: 0 0 6px 0;
    padding: 0;
}
.panel p {
    color: var(--ink-soft) !important;
    margin: 0;
    font-size: 15px;
    line-height: 1.55;
}

/* ---------- Panduan operator ---------- */
.ops {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 4px 0 20px 0;
}
.op {
    display: flex;
    align-items: baseline;
    gap: 10px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    color: var(--ink-soft);
}
.op code {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 14px;
    color: var(--teal-deep);
    background: var(--teal-tint);
    padding: 2px 8px;
    border-radius: 5px;
}

.note {
    background: var(--amber-tint);
    border: 1px solid #EBD08A;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 18px;
    color: var(--ink);
    font-size: 15px;
    line-height: 1.6;
}
.note b { color: var(--ink); }

/* ---------- Input ---------- */
.stTextInput label, .stTextArea label, .stTextInput label p, .stTextArea label p {
    font-weight: 600 !important;
    color: var(--ink) !important;
}
.stTextInput input, .stTextArea textarea {
    background: var(--surface) !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--line) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 16px !important;
    padding: 12px 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px rgba(15,118,110,0.18) !important;
}

/* ---------- Tombol ---------- */
.stButton > button {
    background: var(--teal);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    font-size: 15px;
    transition: background 0.15s ease;
}
.stButton > button:hover { background: var(--teal-deep); color: #FFFFFF; }
.stButton > button:focus-visible { outline: 3px solid var(--amber); outline-offset: 2px; color: #FFFFFF; }
.stButton > button p { color: #FFFFFF !important; }

/* ---------- Tab ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 2px solid var(--line);
    background: transparent;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    height: auto;
    padding: 12px 20px;
    font-weight: 600;
    color: var(--ink-soft);
    background: transparent;
    border-radius: 8px 8px 0 0;
}
.stTabs [aria-selected="true"] { color: var(--teal-deep) !important; background: var(--teal-tint); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--teal); height: 3px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ---------- Tabel kebenaran ---------- */
.tt-wrap {
    overflow-x: auto;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    margin: 12px 0 20px 0;
}
.tt {
    width: 100%;
    border-collapse: collapse;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
}
.tt th {
    background: var(--ink);
    color: #F1F5F2;
    padding: 13px 16px;
    text-align: center;
    font-weight: 600;
    border-right: 1px solid rgba(255,255,255,0.10);
}
.tt th.tt-result { background: var(--teal-deep); border-right: none; }
.tt td {
    padding: 10px 16px;
    text-align: center;
    border-bottom: 1px solid var(--line);
    border-right: 1px solid var(--line);
}
.tt td.tt-result { background: #F4FAF8; border-right: none; border-left: 2px solid var(--teal); }
.tt tr:last-child td { border-bottom: none; }
.tt tbody tr:hover td { background: #EDF4F0; }
.tt tbody tr:hover td.tt-result { background: #E4F3EF; }
.tt tr.tt-bad td { background: #FDF3F0; }
.tt tr.tt-bad td.tt-result { background: #FBE6E0; border-left: 2px solid var(--brick); }

.pill {
    display: inline-block;
    min-width: 32px;
    padding: 3px 0;
    border-radius: 6px;
    font-weight: 600;
    font-size: 14px;
}
.pill-b { background: var(--teal-tint); color: var(--teal-deep); }
.pill-s { background: var(--brick-tint); color: #8E3220; }

/* ---------- Hasil klasifikasi ---------- */
.verdict {
    border-radius: 10px;
    padding: 18px 22px;
    margin-top: 6px;
    border: 1.5px solid;
}
.verdict .label { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.verdict .value {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 24px;
    font-weight: 800;
    line-height: 1.2;
}
.tone-true  { background: var(--teal-tint);  border-color: var(--teal);  color: var(--teal-deep); }
.tone-false { background: var(--brick-tint); border-color: var(--brick); color: #8E3220; }
.tone-mixed { background: var(--amber-tint); border-color: var(--amber); color: #6B4E0F; }

.verdict-detail { font-size: 15px; font-weight: 500; margin-top: 6px; }

/* ---------- Kode & footer ---------- */
.stCode, .stCodeBlock { border-radius: 8px !important; }
.footer {
    text-align: center;
    color: var(--ink-soft);
    font-size: 13px;
    padding: 28px 0 8px 0;
    margin-top: 28px;
    border-top: 1px solid var(--line);
}

/* ---------- Responsif ---------- */
@media (max-width: 640px) {
    .hero { padding: 24px 20px; }
    .hero h1 { font-size: 28px; }
    .hero-mini { display: none; }
}
@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; }
}
</style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 5. HEADER
# =========================================================

md(
    """
    <div class="hero">
      <div>
        <h1>Simulator Tabel Kebenaran</h1>
        <p>Hitung tabel kebenaran ekspresi logika dan periksa apakah sebuah argumen valid.</p>
      </div>
      <table class="hero-mini">
        <tr><th>P</th><th>Q</th><th>P &amp; Q</th></tr>
        <tr><td class="hb">B</td><td class="hb">B</td><td class="hb">B</td></tr>
        <tr><td class="hb">B</td><td class="hs">S</td><td class="hs">S</td></tr>
        <tr><td class="hs">S</td><td class="hb">B</td><td class="hs">S</td></tr>
        <tr><td class="hs">S</td><td class="hs">S</td><td class="hs">S</td></tr>
      </table>
    </div>
    """
)


# =========================================================
# 6. TABS
# =========================================================

tab1, tab2 = st.tabs(
    [
        "📊 Simulator Tabel Kebenaran",
        "⚔️ Verifikator Argumen"
    ]
)


# =========================================================
# TAB 1
# =========================================================

with tab1:

    md(
        """
        <div class="panel">
          <h2>Evaluasi ekspresi logika</h2>
          <p>Tulis satu ekspresi, lalu lihat semua kemungkinan nilainya dan jenis ekspresinya.</p>
        </div>
        """
    )

    md(
        """
        <div class="ops">
          <div class="op"><code>~P / ¬P / NOT P</code> negasi</div>
          <div class="op"><code>P &amp; Q / P ^ Q / AND</code> dan</div>
          <div class="op"><code>P | Q / OR</code> atau</div>
          <div class="op"><code>P -&gt; Q</code> implikasi</div>
          <div class="op"><code>P &lt;-&gt; Q</code> biimplikasi</div>
        </div>
        """
    )

    user_expr = st.text_input(
        "Ekspresi logika",
        value="(P -> Q) & P",
        placeholder="Contoh: (P -> Q) & P"
    )

    if st.button("Buat tabel kebenaran", key="generate_table"):

        if user_expr.strip():

            try:
                vars_list, rows, results = generate_truth_table(user_expr)
            except ValueError as e:
                st.error(f"Ekspresi tidak valid: {e}")
                rows = None

            if rows:

                st.markdown("### Tabel kebenaran")
                render_custom_table(rows)

                status = classify_expression(results)

                md(
                    f"""
                    <div class="verdict {classification_style(status)}">
                      <div class="label">Jenis ekspresi</div>
                      <div class="value">{status}</div>
                    </div>
                    """
                )

            elif rows is not None:

                st.warning(
                    "Variabel tidak ditemukan. "
                    "Gunakan huruf seperti P, Q, atau R."
                )

        else:
            st.warning("Ekspresi masih kosong.")


# =========================================================
# TAB 2
# =========================================================

with tab2:

    md(
        """
        <div class="panel">
          <h2>Verifikasi validitas argumen</h2>
          <p>Masukkan premis dan konklusi untuk memeriksa apakah argumennya valid.</p>
        </div>
        """
    )

    md(
        """
        <div class="note">
          Argumen <b>valid</b> jika bentuk
          <b>(Premis₁ ∧ Premis₂ ∧ …) → Konklusi</b>
          adalah <b>tautologi</b>, yaitu selalu bernilai Benar.
        </div>
        """
    )

    premis_input = st.text_area(
        "Premis (satu premis per baris)",
        value="P -> Q\n~Q",
        height=120,
        placeholder="Contoh:\nP -> Q\n~Q"
    )

    konklusi_input = st.text_input(
        "Konklusi",
        value="~P",
        placeholder="Contoh: ~P"
    )

    if st.button("Periksa argumen", key="verify_argument"):

        premis_list = [
            p.strip()
            for p in premis_input.split("\n")
            if p.strip()
        ]

        if not premis_list:
            st.warning("Isi minimal satu premis.")
        elif not konklusi_input.strip():
            st.warning("Konklusi masih kosong.")
        else:
            combined_premis = " & ".join(f"({p})" for p in premis_list)
            full_argument = f"({combined_premis}) -> ({konklusi_input.strip()})"

            st.markdown("### Bentuk implikasi argumen")
            st.code(full_argument, language="text")

            try:
                vars_list, rows, results, counter = check_argument(
                    premis_list, konklusi_input.strip()
                )
            except ValueError as e:
                st.error(f"Ekspresi tidak valid: {e}")
            else:
                st.markdown("### Tabel kebenaran argumen")
                render_custom_table(rows, highlight_rows=True)

                if all(results):

                    md(
                        """
                        <div class="verdict tone-true">
                          <div class="value">✅ Argumen valid</div>
                          <div class="verdict-detail">Bentuk implikasinya adalah tautologi.</div>
                        </div>
                        """
                    )

                else:

                    contoh = htmllib.escape(format_counterexample(counter[0], vars_list))

                    md(
                        f"""
                        <div class="verdict tone-false">
                          <div class="value">❌ Argumen tidak valid</div>
                          <div class="verdict-detail">
                            Ada {len(counter)} kombinasi nilai yang menghasilkan Salah.
                            Contoh penyangkal: {contoh}
                            (semua premis Benar, tetapi konklusi Salah).
                          </div>
                        </div>
                        """
                    )


# =========================================================
# FOOTER
# =========================================================

md(
    """
    <div class="footer">
      Simulator Tabel Kebenaran · PJBL-1 · Matematika Diskrit
    </div>
    """
)