#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio Piegus — generator strony (PL + EN).

Użycie:   python3 build_site.py
Wynik:    folder ./site  (gotowy do wgrania na hosting)

Wszystko, czego nie wiem o pracowni (telefon, e-mail, ceny, grafik…), uzupełnij w CONFIG poniżej
i uruchom skrypt ponownie. Nieuzupełnione pola są na stronie podświetlone na żółto: [tak].
"""
import html, json, os, random, shutil, urllib.parse

# ───────────────────────────── CONFIG ─────────────────────────────
CONFIG = dict(
    DOMAIN="https://TWOJA-DOMENA.pl",       # adres strony, bez ukośnika na końcu (canonical, hreflang, sitemap)
    PHONE="",                               # np. "+48 600 000 000"
    PHONE_DISPLAY="",                       # jak ma wyglądać na stronie; puste = jak PHONE
    EMAIL="",                               # np. "pracownia@twojadomena.pl"
    STREET_NO="",                           # numer budynku przy ul. Jana III Sobieskiego
    INSTAGRAM="",                           # pełny URL profilu
    FACEBOOK="",                            # pełny URL strony / Messengera
    FORM_ENDPOINT="",                       # opcjonalnie: adres usługi formularzy (Formspree, Getform…). Puste = formularz otwiera gotowego maila
    GTM_ID="",                              # opcjonalnie: GTM-XXXXXXX (pamiętaj o zgodzie na cookies)
    REVIEW_MARKS=True,                      # True = podświetla treści do potwierdzenia; ustaw False przed publikacją
    # Ceny (podaj tekst, np. "240 zł / miesiąc")
    PRICE_ADULT="", PRICE_KIDS="", PRICE_WORKSHOP="", PRICE_VOUCHER_1="", PRICE_VOUCHER_2="", PRICE_GLAZE="",
    # Opinie z Google: lista słowników {"text_pl":…, "text_en":…, "who":"Imię"}; wklejaj prawdziwe opinie
    REVIEWS=[],
    # Grafik: lista (dzień 1–7, "16:00–18:00", "adult"|"kids7"|"kids11", "prowadząca"); None = przykładowy, podświetlony
    TIMETABLE=None,
    # Wolne terminy warsztatów: lista tekstów; None = przykładowe, podświetlone
    FREE_DATES=None,
    KIDS_TEACHER="",                        # imię osoby prowadzącej zajęcia dzieci
)
C = CONFIG
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_src")

LANG = "pl"
def L(pl, en): return pl if LANG == "pl" else en
def esc(s): return html.escape(s, quote=True)

# ───────────────────────────── Helpery ─────────────────────────────
PAGES = {  # klucz: (slug PL, slug EN)
    "home": ("index.html", "index.html"),
    "classes": ("zajecia.html", "classes.html"),
    "kids": ("dzieci.html", "kids.html"),
    "workshops": ("warsztaty.html", "workshops.html"),
    "voucher": ("bon.html", "voucher.html"),
    "teams": ("firmy.html", "teams.html"),
    "prices": ("ceny.html", "prices.html"),
    "members": ("uczestnicy.html", "members.html"),
    "contact": ("kontakt.html", "contact.html"),
}
def slug(key, lang): return PAGES[key][0 if lang == "pl" else 1]
def url(key, frag=""):
    return slug(key, LANG) + (("#" + frag) if frag else "")
def other_url(key):
    return ("en/" + slug(key, "en")) if LANG == "pl" else ("../" + slug(key, "pl"))
def asset(p): return ("" if LANG == "pl" else "../") + "assets/" + p
def home_url(): return "index.html"
def abs_url(key, lang):
    return C["DOMAIN"] + ("/" if lang == "pl" else "/en/") + ("" if slug(key, lang) == "index.html" else slug(key, lang))

def fill(label, val=""):
    return esc(val) if val else '<mark class="fill">[%s]</mark>' % esc(label)
def chk(text):
    """Treść wymyślona na podstawie strategii — do potwierdzenia przez właścicielkę."""
    return '<mark class="fill" title="Potwierdź lub popraw">%s</mark>' % text if C["REVIEW_MARKS"] else text
def price(key, label):
    return fill(label, C[key])

def tel_href():
    return "tel:" + C["PHONE"].replace(" ", "") if C["PHONE"] else url("contact", "formularz")
def tel_text():
    return fill(L("telefon", "phone"), C["PHONE_DISPLAY"] or C["PHONE"])
def mail_href():
    return "mailto:" + C["EMAIL"] if C["EMAIL"] else url("contact", "formularz")
def mail_text():
    return fill("e-mail", C["EMAIL"])

MAPS_Q = "Studio Piegus Jana III Sobieskiego Warszawa"
MAPS_LINK = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(MAPS_Q)
MAPS_EMBED = "https://www.google.com/maps?q=" + urllib.parse.quote(MAPS_Q) + "&output=embed"

ARROW = '<svg viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg>'

DAYS_PL = {1: "Poniedziałek", 2: "Wtorek", 3: "Środa", 4: "Czwartek", 5: "Piątek", 6: "Sobota", 7: "Niedziela"}
DAYS_EN = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
def dayname(d): return (DAYS_PL if LANG == "pl" else DAYS_EN)[d]
GROUPS = {
    "adult": ("Dorośli i młodzież 15+", "Adults and teens 15+"),
    "kids7": ("Dzieci 7–10 lat", "Children 7–10"),
    "kids11": ("Dzieci 11–14 lat", "Children 11–14"),
}
def groupname(g): return L(*GROUPS[g])

SAMPLE_TT = [
    (1, "16:00–18:00", "adult", "Zuzanna"), (3, "17:00–19:00", "adult", "Zuzanna"),
    (4, "18:00–20:00", "adult", "Zuzanna"), (6, "11:00–13:00", "adult", "Zuzanna"),
    (2, "16:00–17:00", "kids7", "Zuzanna"), (4, "16:00–17:00", "kids11", "Zuzanna"),
    (6, "10:00–11:00", "kids7", "Zuzanna"),
]
def tt_rows(kinds):
    rows = C["TIMETABLE"] if C["TIMETABLE"] is not None else SAMPLE_TT
    return [r for r in sorted(rows, key=lambda r: (r[0], r[1])) if r[2] in kinds]
def tt_is_sample(): return C["TIMETABLE"] is None
SAMPLE_DATES = [("sob. 24.10, 11:00", "Sat 24 Oct, 11:00"), ("niedz. 25.10, 12:00", "Sun 25 Oct, 12:00"), ("sob. 31.10, 11:00", "Sat 31 Oct, 11:00")]
def free_dates():
    if C["FREE_DATES"] is not None:
        return list(C["FREE_DATES"]), False
    return [L(a, b) for a, b in SAMPLE_DATES], True

def timetable(kinds):
    rows = tt_rows(kinds)
    days = sorted({r[0] for r in rows})
    sample = tt_is_sample()
    out = ['<div data-tt>']
    out.append('<p class="chip-label">%s</p><div class="chips" role="group" aria-label="%s">' % (L("Który dzień Ci pasuje?", "Which day suits you?"), L("Filtr dni", "Day filter")))
    out.append('<button type="button" class="chip" data-filter="day" data-value="all" aria-pressed="true">%s</button>' % L("Wszystkie", "All"))
    for d in days:
        out.append('<button type="button" class="chip" data-filter="day" data-value="%d" aria-pressed="false">%s</button>' % (d, dayname(d)))
    out.append('</div><div class="tt" role="list">')
    for d, t, g, who in rows:
        val = "%s %s" % (dayname(d), t)
        cell_day = '<mark class="fill">%s</mark>' % dayname(d) if (sample and C["REVIEW_MARKS"]) else dayname(d)
        cell_time = '<mark class="fill">%s</mark>' % t if (sample and C["REVIEW_MARKS"]) else t
        teacher = who
        if g != "adult" and C["KIDS_TEACHER"] and C["TIMETABLE"] is None:
            teacher = C["KIDS_TEACHER"]
        out.append('<div class="tt-row" role="listitem" data-day="%d" data-group="%s"><span class="tt-day">%s</span><span class="tt-time">%s</span><span>%s</span><span class="tt-who">%s</span><a class="btn ghost" href="#zapis" data-pick="%s">%s</a></div>'
                   % (d, g, cell_day, cell_time, groupname(g), esc(teacher), esc(val), L("Zapisz się", "Join")))
    out.append('<p class="tt-empty" hidden>%s</p></div></div>' % L("W tym dniu nie ma zajęć. Wybierz inny dzień albo napisz — poszukamy miejsca.", "No classes on that day. Pick another day or write to us, and we will look for a place."))
    return "".join(out)

def group_options(kinds):
    opts = ['<option value="">%s</option>' % L("Wybierz grupę", "Choose a group")]
    for d, t, g, who in tt_rows(kinds):
        v = "%s %s" % (dayname(d), t)
        opts.append('<option value="%s">%s, %s — %s</option>' % (esc(v), dayname(d), t, groupname(g)))
    opts.append('<option value="%s">%s</option>' % (L("Nie wiem jeszcze — doradźcie", "Not sure yet — advise me"), L("Nie wiem jeszcze — doradźcie", "Not sure yet — advise me")))
    return "".join(opts)

# ───────────────────────────── Formularze ─────────────────────────────
def fld(name, label, typ="text", req=False, hint="", options=None, rows=0, ac=""):
    fid = "f-" + name
    lab = '<label for="%s">%s%s</label>' % (fid, label, (' <span class="hint">%s</span>' % hint) if hint else "")
    r = " required" if req else ""
    a = (' autocomplete="%s"' % ac) if ac else ""
    if options is not None:
        inner = options if isinstance(options, str) else "".join('<option value="%s">%s</option>' % (esc(o), esc(o)) for o in options)
        ctl = '<select id="%s" name="%s"%s>%s</select>' % (fid, name, r, inner)
    elif rows:
        ctl = '<textarea id="%s" name="%s" rows="%d"%s></textarea>' % (fid, name, rows, r)
    else:
        ctl = '<input id="%s" name="%s" type="%s"%s%s>' % (fid, name, typ, r, a)
    return '<div class="field">%s%s</div>' % (lab, ctl)

def form(kind, title, intro, fields_html, button, subject, fid="zapis"):
    return ('<form class="form" id="%s" data-form="%s" data-subject="%s" data-ok="%s" data-err="%s" data-mail="%s" novalidate-off>'
            '<h2>%s</h2><p class="intro">%s</p>%s'
            '<div class="hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>'
            '<button class="btn" type="submit">%s</button><p class="form-status" role="status" aria-live="polite"></p>'
            '<p class="privacy">%s</p></form>') % (
        fid, kind, esc(subject),
        esc(L("Dziękujemy. Odpiszemy najszybciej, jak się da.", "Thank you. We will reply as soon as we can.")),
        esc(L("Nie udało się wysłać. Zadzwoń albo napisz bezpośrednio na e-mail.", "That did not go through. Call us or write to the email address directly.")),
        esc(L("Otwieramy Twoją pocztę z gotową wiadomością — wystarczy kliknąć „Wyślij”.", "Opening your email app with the message ready. Just press send.")),
        title, intro, fields_html, button,
        L("Wykorzystamy te dane wyłącznie po to, żeby odpowiedzieć na Twoją wiadomość.", "We use these details only to answer your message."))

def contact_fields():
    return (fld("imie", L("Imię", "Name"), req=True, ac="given-name") +
            fld("kontakt", L("Telefon lub e-mail", "Phone or email"), req=True, ac="email"))

def form_join():
    f = fld("grupa", L("Grupa, która Cię interesuje", "Group you are interested in"), options=group_options(["adult"]))
    f += contact_fields()
    f += fld("wiadomosc", L("Co chcesz wiedzieć?", "Anything you want to ask?"), hint=L("(nie musisz nic pisać)", "(optional)"), rows=4)
    return form("zapis-dorosli", L("Chcę dołączyć do grupy", "I want to join a group"),
                L("Napisz, która grupa Ci pasuje. Odpisze Zuzanna albo ktoś z nas, a nie automat.", "Tell us which group suits you. Zuzanna or one of us will answer, not a bot."),
                f, L("Wyślij", "Send"), L("Zapis na zajęcia", "Class enrolment"))

def form_kids():
    f = fld("grupa", L("Grupa", "Group"), options=group_options(["kids7", "kids11"]))
    f += fld("wiek", L("Ile lat ma dziecko?", "How old is your child?"), req=True)
    f += fld("imie", L("Twoje imię", "Your name"), req=True, ac="given-name")
    f += fld("kontakt", L("Telefon lub e-mail", "Phone or email"), req=True, ac="email")
    f += fld("wiadomosc", L("Co chcesz wiedzieć?", "Anything you want to ask?"), hint=L("(nie musisz nic pisać)", "(optional)"), rows=3)
    return form("zapis-dzieci", L("Zapisz dziecko albo zapytaj o miejsce", "Enrol your child or ask about a place"),
                L("Wolisz zadzwonić? Numer jest obok. Jeśli wolisz napisać, odezwiemy się szybko.", "Prefer to call? The number is next to this form. If you would rather write, we will get back to you quickly."),
                f, L("Wyślij", "Send"), L("Zapis dziecka", "Child enrolment"))

def form_group():
    dates, _ = free_dates()
    f = '<div class="row2">' + fld("osoby", L("Ile osób?", "How many people?"), options=[str(i) for i in range(1, 9)]) + fld("okazja", L("Okazja", "Occasion"), options=[L("Urodziny", "Birthday"), L("Wieczór panieński", "Bachelorette"), L("Dzień Kobiet", "Women’s Day"), L("Prezent", "Gift"), L("Spotkanie przyjaciół", "Friends getting together"), L("Inna", "Other")]) + '</div>'
    f += fld("terminy", L("Pasujące terminy", "Dates that work"), req=True, hint=L("(podaj dwa–trzy; odpiszemy z konkretnymi propozycjami)", "(give two or three; we will reply with concrete options)"))
    f += fld("imie", L("Imię", "Name"), req=True, ac="given-name") + fld("kontakt", L("Telefon lub e-mail", "Phone or email"), req=True, ac="email")
    f += fld("wiadomosc", L("Coś jeszcze?", "Anything else?"), hint=L("(opcjonalnie)", "(optional)"), rows=3)
    return form("warsztat-grupa", L("Zapytaj o termin dla grupy", "Ask about a date for your group"),
                L("Podaj dwa–trzy terminy. Odpiszemy z dwoma–trzema wolnymi, żeby nie zaczynać negocjacji od nowa.", "Give us two or three dates. We will reply with two or three free ones, so you do not have to restart the negotiation."),
                f, L("Zapytaj o termin", "Ask about a date"), L("Warsztat dla grupy", "Group workshop"))

def form_voucher():
    f = fld("rodzaj", L("Co kupujesz?", "What are you buying?"), options=[L("Bon na warsztat — jedna osoba", "Workshop voucher — one person"), L("Bon na warsztat — dwie osoby", "Workshop voucher — two people"), L("Bon na serię zajęć", "Voucher for a run of classes"), L("Nie wiem — doradźcie", "Not sure — advise me")])
    f += fld("odbior", L("Jak ma do Ciebie trafić?", "How should it reach you?"), options=[L("PDF na e-mail", "PDF by email"), L("Wersja drukowana do odbioru w pracowni", "Printed copy to collect at the studio"), L("Zadzwońcie do mnie", "Call me")])
    f += fld("potrzebny", L("Na kiedy potrzebujesz bonu?", "When do you need it by?"), hint=L("(data okazji)", "(date of the occasion)"))
    f += fld("dla", L("Dla kogo?", "Who is it for?"), hint=L("(imię na bonie — opcjonalnie)", "(name on the voucher — optional)"))
    f += fld("imie", L("Twoje imię", "Your name"), req=True, ac="given-name") + fld("kontakt", L("Telefon lub e-mail", "Phone or email"), req=True, ac="email")
    return form("bon", L("Zamów bon", "Order a voucher"),
                L("Po wysłaniu odpiszemy z danymi do przelewu. Pilne? Zadzwoń — to szybsze.", "After you send this we reply with the transfer details. In a hurry? Call. It is faster."),
                f, L("Zamów bon", "Order voucher"), L("Zamówienie bonu", "Voucher order"))

def form_team():
    f = fld("firma", L("Firma", "Company"), req=True, ac="organization")
    f += '<div class="row2">' + fld("osoby", L("Ile osób w zespole?", "How many people?"), req=True) + fld("termin", L("Kiedy? (data albo miesiąc)", "When? (date or month)")) + '</div>'
    f += fld("miejsce", L("Gdzie?", "Where?"), options=[L("U nas w biurze", "At our office"), L("W pracowni", "At the studio"), L("Jeszcze nie wiemy", "We have not decided")])
    f += '<div class="row2">' + fld("imie", L("Imię i nazwisko", "Your name"), req=True, ac="name") + fld("email", "E-mail", "email", req=True, ac="email") + '</div>'
    f += fld("telefon", L("Telefon", "Phone"), hint=L("(opcjonalnie)", "(optional)"), ac="tel")
    f += fld("wiadomosc", L("Co jeszcze warto wiedzieć?", "Anything we should know?"), hint=L("(np. okazja, dwie osoby, które „nie lubią takich rzeczy”)", "(for example the occasion, or the two people who “don’t do this sort of thing”)"), rows=4)
    return form("firmy", L("Poproś o propozycję", "Ask for a proposal"),
                L("Napisz, ilu Was jest i kiedy. W odpowiedzi dostaniesz gotowy scenariusz z jedną ceną, a nie listę pytań.", "Tell us how many of you there are and when. You get back a ready scenario with one price, not a list of questions."),
                f, L("Wyślij zapytanie", "Send request"), L("Zapytanie firmowe", "Corporate enquiry"))

def form_contact():
    f = fld("temat", L("O czym chcesz napisać?", "What is this about?"), options=[L("Zajęcia regularne", "Regular classes"), L("Zajęcia dla dziecka", "Classes for my child"), L("Warsztat z przyjaciółmi", "Workshop with friends"), L("Bon", "Gift voucher"), L("Zajęcia dla zespołu", "Team workshop"), L("Coś innego", "Something else")])
    f += contact_fields()
    f += fld("wiadomosc", L("Wiadomość", "Message"), req=True, rows=5)
    return form("kontakt", L("Napisz do nas", "Write to us"),
                L("Każda wiadomość trafia do człowieka. Odpowiadamy sami.", "Every message reaches a person. We answer them ourselves."),
                f, L("Wyślij", "Send"), L("Wiadomość ze strony", "Message from the website"), fid="formularz")

# ───────────────────────────── Ilustracje ─────────────────────────────
def speckle_dots(seed, n, w, h, colors, rmin=.9, rmax=2.8):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(rmin, rmax) ** 1.0
        op = rnd.uniform(.35, .85)
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="%.2f"/>' % (x, y, r, rnd.choice(colors), op))
    return "".join(out)

def vessel_svg():
    dots = speckle_dots(7, 95, 420, 520, ["#6B3F26", "#6B3F26", "#3A2214"], .8, 2.6)
    body = "M150 456 C118 436 74 372 80 300 C86 238 148 208 160 166 C166 142 150 122 140 98 L272 94 C262 120 246 140 250 170 C258 212 338 244 342 312 C346 384 304 432 272 456 Z"
    glaze = "M-20 -140 H440 V318 C395 332 372 312 346 334 C324 352 312 338 300 372 C292 396 276 396 270 360 C266 340 240 330 226 348 C214 362 214 420 200 424 C186 428 184 362 168 352 C148 340 130 366 110 346 C90 330 60 344 -20 326 Z"
    return ('<svg class="vessel" viewBox="0 0 420 520" role="img" aria-label="%s">'
            '<defs><clipPath id="vb"><path d="%s"/></clipPath><clipPath id="bowl"><path d="M18 470 H122 C122 502 96 514 70 514 C44 514 18 502 18 470 Z"/></clipPath></defs>'
            '<ellipse cx="215" cy="482" rx="160" ry="15" fill="#1C2733" opacity=".13"/>'
            '<g clip-path="url(#vb)"><rect x="0" y="0" width="420" height="520" fill="#D8C7AC"/>'
            '<g class="glaze-drip"><path d="%s" fill="#2B4BA0"/></g>'
            '<path d="M112 300 C106 252 146 226 156 190" stroke="#fff" stroke-opacity=".22" stroke-width="12" fill="none" stroke-linecap="round"/>'
            '%s</g>'
            '<ellipse cx="206" cy="96" rx="67" ry="11" fill="#14245A"/><ellipse cx="206" cy="96" rx="67" ry="11" fill="none" stroke="#1B2F6B" stroke-width="3"/>'
            '<g clip-path="url(#bowl)"><rect x="10" y="460" width="130" height="60" fill="#D9A12B"/>'
            '<path d="M10 520 V496 C40 488 80 504 140 492 V520Z" fill="#D8C7AC"/>%s</g>'
            '<ellipse cx="70" cy="470" rx="52" ry="8" fill="#8C6414"/>'
            '</svg>') % (L("Ręcznie lepiona waza w kobaltowym szkliwie i mała ochrowa miseczka", "A hand-built vase in cobalt glaze and a small ochre bowl"),
                          body, glaze, dots, speckle_dots(3, 16, 140, 60, ["#6B3F26"], .7, 1.8))

def pinch_pot_svg():
    return ('<svg viewBox="0 0 200 200" width="130" height="130" aria-hidden="true"><path d="M38 124 C18 104 28 62 70 56 C110 46 152 62 160 98 C168 134 150 160 102 162 C62 164 50 142 38 124 Z" fill="#D8C7AC" stroke="#1C2733" stroke-width="3"/>'
            '<path d="M70 100 C86 90 118 92 132 104" stroke="#1C2733" stroke-width="3" fill="none" stroke-linecap="round" opacity=".55"/>'
            '<g fill="#6B3F26"><circle cx="60" cy="80" r="2"/><circle cx="118" cy="72" r="2.4"/><circle cx="140" cy="120" r="2"/><circle cx="84" cy="138" r="2.2"/><circle cx="104" cy="148" r="1.6"/></g></svg>')

def cup_svg():
    return ('<svg viewBox="0 0 200 200" width="130" height="130" aria-hidden="true"><path d="M148 82 C186 78 186 128 142 128" fill="none" stroke="#1C2733" stroke-width="3"/>'
            '<path d="M48 56 H148 C148 122 136 166 98 166 C60 166 48 122 48 56 Z" fill="#9DBDAB" stroke="#1C2733" stroke-width="3"/>'
            '<path d="M49 80 H147" stroke="#2B4BA0" stroke-width="12"/><ellipse cx="98" cy="56" rx="50" ry="8" fill="#6E9381" stroke="#1C2733" stroke-width="3"/>'
            '<g fill="#6B3F26"><circle cx="70" cy="110" r="2"/><circle cx="118" cy="120" r="2.2"/><circle cx="96" cy="140" r="1.8"/><circle cx="130" cy="98" r="1.6"/><circle cx="74" cy="138" r="1.6"/></g></svg>')

def dots_svg():
    return '<svg class="v-dot" viewBox="0 0 50 50" aria-hidden="true"><circle cx="25" cy="25" r="22" fill="#2B4BA0"/>%s</svg>' % speckle_dots(5, 14, 50, 50, ["#F6F5F1"], .8, 1.8)

# ───────────────────────────── Szkielet ─────────────────────────────
NAV = [("classes", "Zajęcia", "Classes"), ("kids", "Dzieci", "Kids"), ("workshops", "Warsztaty", "Workshops"),
       ("voucher", "Bon", "Gift voucher"), ("teams", "Dla firm", "For teams"), ("prices", "Ceny i zasady", "Prices & rules"), ("contact", "Kontakt", "Contact")]

META = {
    "home": ("Studio Piegus — pracownia ceramiki w Sadybie, Warszawa", "Studio Piegus — ceramics studio in Sadyba, Warsaw",
             "Zajęcia ceramiki w małych grupach w Sadybie. Nie musisz nic umieć — glinę, narzędzia i fartuch masz na miejscu. Od 2019 roku.",
             "Small-group pottery classes in Sadyba, Warsaw. No experience needed — clay, tools and an apron are here. Since 2019."),
    "classes": ("Zajęcia ceramiki dla dorosłych — Sadyba | Studio Piegus", "Pottery classes for adults — Sadyba | Studio Piegus",
                "Regularne zajęcia ceramiki dla dorosłych i młodzieży 15+. Dwie godziny, co tydzień lub co dwa tygodnie. Płatność miesięczna, bez długiego zobowiązania.",
                "Regular pottery classes for adults and teens 15+. Two hours, weekly or fortnightly. Paid monthly, no long commitment."),
    "kids": ("Zajęcia ceramiki dla dzieci 7–14 lat — Sadyba | Studio Piegus", "Pottery classes for children 7–14 — Sadyba | Studio Piegus",
             "Godzinne zajęcia ceramiki dla dzieci 7–14 lat w małych grupach. Grupy według wieku, godziny dopasowane do szkoły.",
             "One-hour pottery classes for children aged 7–14, in small groups. Groups by age, hours that fit around school."),
    "workshops": ("Warsztat ceramiczny dla przyjaciół i par — Warszawa | Studio Piegus", "Pottery workshop for friends and couples — Warsaw | Studio Piegus",
                  "Warsztat ceramiczny dla 1–8 osób, ok. 3,5 godziny, bez doświadczenia. Urodziny, wieczór panieński, spotkanie przyjaciół.",
                  "A pottery workshop for 1–8 people, about 3.5 hours, no experience needed. Birthdays, bachelorette parties, friends getting together."),
    "voucher": ("Bon na warsztat ceramiczny — prezent w Warszawie | Studio Piegus", "Pottery workshop gift voucher — Warsaw | Studio Piegus",
                "Bon na warsztat ceramiczny lub serię zajęć, ważny pół roku. Wersja PDF i drukowana. Obdarowany sam wybiera termin.",
                "A voucher for a pottery workshop or a run of classes, valid for six months. PDF and printed versions. The recipient picks their own date."),
    "teams": ("Integracja firmowa: warsztat ceramiczny dla zespołu | Studio Piegus", "Team workshop: pottery for companies | Studio Piegus",
              "Warsztat ceramiczny dla zespołu: u Was w biurze albo w naszej pracowni. Scenariusz, harmonogram, jedna cena, faktura.",
              "A pottery workshop for teams, at your office or in our studio. Scenario, timings, one price, a proper invoice."),
    "prices": ("Ceny i zasady | Studio Piegus", "Prices and rules | Studio Piegus",
               "Co jest w cenie, co kosztuje dodatkowo, jak płacisz i co z nieobecnościami. Zajęcia, warsztaty, bony.",
               "What is included, what costs extra, how you pay and what happens if you miss a class."),
    "members": ("Dla uczestników zajęć | Studio Piegus", "For current participants | Studio Piegus",
                "Odrabianie zajęć, odbiór prac po wypale, cena wypału szkliwa, płatności i kontynuacja.",
                "Making up classes, collecting your work after firing, the cost of glaze firing, payments and continuing."),
    "contact": ("Kontakt i dojazd — Sadyba, Warszawa | Studio Piegus", "Contact and directions — Sadyba, Warsaw | Studio Piegus",
                "Studio Piegus, ul. Jana III Sobieskiego, Sadyba, Warszawa. Zadzwoń albo napisz — odpowiada człowiek.",
                "Studio Piegus, ul. Jana III Sobieskiego, Sadyba, Warsaw. Call or write. A person answers."),
}

def head(key):
    tpl, ten, dpl, den = META[key]
    title, desc = (tpl, dpl) if LANG == "pl" else (ten, den)
    base = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>%s</title>' % esc(title),
        '<meta name="description" content="%s">' % esc(desc),
        '<link rel="canonical" href="%s">' % abs_url(key, LANG),
        '<link rel="alternate" hreflang="pl" href="%s">' % abs_url(key, "pl"),
        '<link rel="alternate" hreflang="en" href="%s">' % abs_url(key, "en"),
        '<link rel="alternate" hreflang="x-default" href="%s">' % abs_url(key, "pl"),
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Studio Piegus">',
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s">' % (esc(title), esc(desc)),
        '<meta property="og:url" content="%s"><meta property="og:locale" content="%s">' % (abs_url(key, LANG), "pl_PL" if LANG == "pl" else "en_GB"),
        '<meta name="theme-color" content="#2B4BA0">',
        '<link rel="icon" href="%s" type="image/svg+xml">' % asset("favicon.svg"),
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap">',
        '<link rel="stylesheet" href="%s">' % asset("style.css"),
        '<script>window.PIEGUS=%s;</script>' % json.dumps({"endpoint": C["FORM_ENDPOINT"], "email": C["EMAIL"]}),
    ]
    if C["GTM_ID"]:
        base.append("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','%s');</script>" % C["GTM_ID"])
    if key == "home":
        ld = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": "Studio Piegus",
              "description": desc, "url": C["DOMAIN"] + "/", "foundingDate": "2019",
              "founder": {"@type": "Person", "name": "Zuzanna Muraszkiewicz"},
              "address": {"@type": "PostalAddress", "streetAddress": "ul. Jana III Sobieskiego" + ((" " + C["STREET_NO"]) if C["STREET_NO"] else ""),
                          "addressLocality": "Warszawa", "addressRegion": "Sadyba", "addressCountry": "PL"},
              "knowsLanguage": ["pl", "en"], "hasMap": MAPS_LINK}
        if C["PHONE"]: ld["telephone"] = C["PHONE"]
        if C["EMAIL"]: ld["email"] = C["EMAIL"]
        same = [u for u in (C["INSTAGRAM"], C["FACEBOOK"]) if u]
        if same: ld["sameAs"] = same
        base.append('<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False))
    return "\n".join(base)

def header(key):
    links = []
    for k, pl, en in NAV:
        cur = ' aria-current="page"' if k == key else ""
        links.append('<a href="%s"%s>%s</a>' % (url(k), cur, L(pl, en)))
    links.append('<a class="lang" href="%s" hreflang="%s" lang="%s" aria-label="%s">%s</a>' % (
        other_url(key), "en" if LANG == "pl" else "pl", "en" if LANG == "pl" else "pl",
        "English version" if LANG == "pl" else "Wersja polska", "EN" if LANG == "pl" else "PL"))
    return ('<a class="skip" href="#main">%s</a><header class="site-header"><div class="wrap">'
            '<a class="logo" href="%s" aria-label="Studio Piegus">Piegus<span class="dots" aria-hidden="true"></span></a>'
            '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav">%s</button>'
            '<nav class="nav" id="nav" aria-label="%s">%s</nav></div></header>') % (
        L("Przejdź do treści", "Skip to content"), home_url(), L("Menu", "Menu"), L("Główna", "Main"), "".join(links))

def footer(key):
    soc = []
    if C["INSTAGRAM"]: soc.append('<li><a href="%s" rel="noopener">Instagram</a></li>' % esc(C["INSTAGRAM"]))
    if C["FACEBOOK"]: soc.append('<li><a href="%s" rel="noopener">Facebook / Messenger</a></li>' % esc(C["FACEBOOK"]))
    if not soc and C["REVIEW_MARKS"]: soc.append('<li><mark class="fill">[Instagram / Facebook]</mark></li>')
    return ('<footer class="site-footer"><div class="wrap"><div class="cols">'
            '<div><a class="logo" href="%s">Piegus<span class="dots" aria-hidden="true"></span></a>'
            '<p>%s</p><p>%s<br>%s</p></div>'
            '<div><h3>%s</h3><ul>%s<li><a href="%s">%s</a></li></ul></div>'
            '<div><h3>%s</h3><ul><li><a href="%s">%s</a></li><li><a href="%s">%s</a></li>%s<li><a href="%s">%s</a></li></ul></div>'
            '</div><p class="small">%s</p></div></footer>') % (
        home_url(),
        L("Pracownia ceramiki w Sadybie. Od 2019 roku. Założona i prowadzona przez Zuzannę Muraszkiewicz.", "A ceramics studio in Sadyba, Warsaw. Since 2019. Founded and run by Zuzanna Muraszkiewicz."),
        "ul. Jana III Sobieskiego %s, Sadyba, Warszawa" % fill(L("nr", "no."), C["STREET_NO"]),
        '<a href="%s">%s</a> · <a href="%s">%s</a>' % (tel_href(), tel_text(), mail_href(), mail_text()),
        L("Oferta", "What we offer"),
        "".join('<li><a href="%s">%s</a></li>' % (url(k), L(pl, en)) for k, pl, en in NAV[:5]),
        url("members"), L("Dla uczestników", "For participants"),
        L("Pracownia", "The studio"),
        url("prices"), L("Ceny i zasady", "Prices and rules"), url("contact"), L("Kontakt i dojazd", "Contact and directions"),
        "".join(soc), other_url(key), "English" if LANG == "pl" else "Polski",
        L("Uczymy po polsku i po angielsku.", "We teach in English as readily as in Polish."))

def mobile_bar():
    return ('<div class="mobile-bar"><a class="btn" href="%s">%s</a><a class="btn ghost" href="%s">%s</a></div>') % (
        tel_href(), L("Zadzwoń", "Call"), url("contact", "formularz"), L("Napisz", "Write"))

def page(key, body):
    gtm_ns = ('<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=%s" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>' % C["GTM_ID"]) if C["GTM_ID"] else ""
    return ('<!doctype html>\n<html lang="%s">\n<head>\n%s\n</head>\n<body>%s\n%s\n<main id="main">%s</main>\n%s\n%s\n<script src="%s" defer></script>\n</body>\n</html>\n') % (
        LANG, head(key), gtm_ns, header(key), body, footer(key), mobile_bar(), asset("site.js"))

# ───────────────────────────── Elementy treści ─────────────────────────────
def phead(title, lead):
    return '<section class="page-head"><div class="wrap"><h1>%s</h1><p class="lead">%s</p></div></section>' % (title, lead)

def section(inner, cls=""):
    return '<section class="section %s"><div class="wrap">%s</div></section>' % (cls, inner)

def reviews_block():
    revs = C["REVIEWS"]
    if revs:
        items = "".join('<blockquote><p>%s</p><cite>%s</cite></blockquote>' % (esc(r["text_pl"] if LANG == "pl" or not r.get("text_en") else r["text_en"]), esc(r["who"])) for r in revs[:3])
        body = '<div class="reviews">%s</div>' % items
    else:
        body = ('<p>%s</p>' % chk(L("[Wklej tu 3 prawdziwe opinie z Google — w pliku build_site.py, pole REVIEWS.]", "[Paste three real Google reviews here — in build_site.py, the REVIEWS field.]"))) if C["REVIEW_MARKS"] else ""
    return section('<h2>%s</h2><p>%s</p>%s<p><a class="btn ghost" href="%s" rel="noopener">%s</a></p>' % (
        L("Co piszą uczestnicy", "What participants write"),
        L("Najczęściej piszą o Zuzannie, o atmosferze i o ludziach w sali. Rzadziej o samych naczyniach.", "They mostly write about Zuzanna, the atmosphere and the people in the room. Less often about the objects they made."),
        body, MAPS_LINK, L("Wszystkie opinie w Google", "All reviews on Google")), "band-celadon")

def cta_band(title, text, primary, secondary=None):
    sec = ('<a class="btn outline-light big" href="%s">%s</a>' % secondary) if secondary else ""
    return section('<h2>%s</h2><p class="lead">%s</p><div class="btns"><a class="btn light big" href="%s">%s</a>%s</div>' % (title, text, primary[0], primary[1], sec), "band-cobalt")

def included_block():
    return ('<div class="incl"><div><h3>%s</h3><ul><li>%s</li><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ul></div>'
            '<div class="extra"><h3>%s</h3><ul><li>%s</li></ul><p>%s</p></div></div>') % (
        L("W cenie", "Included"),
        L("glina, szkliwa, engoby i podszkliwia", "clay, glazes, engobes and underglazes"),
        L("narzędzia i fartuch", "tools and an apron"),
        L("wypał biskwitowy", "bisque firing"),
        L("nauka, z nauczycielem w sali", "teaching, with a teacher in the room"),
        L("miejsce przy stole", "your place at the table"),
        L("Poza ceną", "Not included"),
        L("wypał szkliwa: %s", "glaze firing: %s") % price("PRICE_GLAZE", L("cena wypału szkliwa", "glaze firing price")),
        chk(L("Zapłacisz go przy odbiorze pracy.", "You pay for it when you collect your piece.")))

# ───────────────────────────── STRONY ─────────────────────────────
def p_home():
    hero = ('<section class="hero"><div class="wrap"><div><h1>%s</h1><p class="lead">%s</p>'
            '<div class="btns"><a class="btn big" href="%s">%s</a><a class="btn ghost big" href="%s">%s</a></div></div>%s</div></section>') % (
        L("Chodź polepić.", "Come and make something."),
        L("Mała grupa, ktoś, kto ma dla Ciebie czas, i kilka godzin w Sadybie, w których robisz coś rękami. Nie musisz nic umieć. Fartuch i glinę masz na miejscu.",
          "A small group, a teacher who has time for you, and a few hours in Sadyba spent making something with your hands. You don’t need any experience. Clay and an apron are here."),
        url("classes", "grafik"), L("Sprawdź grafik zajęć", "See the class timetable"), url("voucher"), L("Kup bon", "Buy a voucher"), vessel_svg())

    rows = [
        ("classes", L("Chcę mieć jeden wieczór w tygodniu tylko dla siebie.", "I want one evening a week that is just mine."), L("Zajęcia regularne dla dorosłych i młodzieży 15+. Dwie godziny, co tydzień albo co dwa.", "Regular classes for adults and teens 15+. Two hours, weekly or fortnightly.")),
        ("workshops", L("Chcę zrobić coś z przyjaciółkami zamiast kolejnej kolacji.", "I’d rather do something with friends than another dinner."), L("Warsztat dla 1–8 osób, ok. 3,5 godziny, bez doświadczenia.", "A workshop for 1–8 people, about 3.5 hours, no experience needed.")),
        ("voucher", L("Szukam prezentu, który nie wygląda jak każdy inny.", "I’m looking for a present that doesn’t look like every other present."), L("Bon na warsztat lub serię zajęć. Ważny pół roku. PDF od ręki.", "A voucher for a workshop or a run of classes. Valid six months. PDF straight away.")),
        ("kids", L("Moje dziecko lubi robić rzeczy rękami.", "My child likes making things with their hands."), L("Zajęcia dla dzieci 7–14 lat. Godzina tygodniowo, z nauczycielem, który ma na imię.", "Classes for children aged 7–14. One hour a week, with a teacher who has a name.")),
        ("teams", L("Szukam integracji dla zespołu. Bez slajdów.", "I need a team event. Without the slides."), L("Przyjeżdżamy do Was albo zapraszamy do pracowni.", "We come to your office, or you come to us.")),
    ]
    router = section('<h2>%s</h2><ul class="router">%s</ul>' % (
        L("Po co do nas zaglądasz?", "What brings you here?"),
        "".join('<li><a href="%s"><span class="say">%s</span><span class="what">%s</span><span class="go">%s</span></a></li>' % (url(k), s, w, ARROW) for k, s, w in rows)))

    two = section('<div class="two"><h2>%s</h2><div><p>%s</p><p>%s</p><p>%s</p></div></div>' % (
        L("Co się dzieje przez dwie godziny", "What happens in two hours"),
        L("Wchodzisz, zakładasz fartuch. Na stole leży glina. Mówisz, co chcesz zrobić: miskę, kubek, coś, czego jeszcze nie umiesz nazwać. Ktoś z nas pokazuje, jak się za to zabrać.",
          "You walk in and put on an apron. There’s clay on the table. You say what you want to make: a bowl, a mug, something you can’t name yet. One of us shows you how to start."),
        L("Przez pierwsze dziesięć minut jest trochę niezręcznie. To normalne. Po dwudziestu ręce wiedzą, co robić, a czas gdzieś znika.",
          "The first ten minutes are a bit awkward. That’s normal. After twenty your hands know what to do and the time goes somewhere."),
        L("Wszyscy w sali robią swoje i nikt nie zagląda Ci przez ramię. Po wypale wracasz po pracę. To najlepszy moment.",
          "Everyone in the room is busy with their own piece and nobody looks over your shoulder. After firing you come back for it. That’s the best moment.")), "band-celadon")

    facts = section('<h2>%s</h2><ul class="facts">%s</ul>' % (
        L("Dlaczego u nas inaczej się uczy", "Why it feels different here"),
        "".join('<li><h3>%s</h3><p>%s</p></li>' % x for x in [
            (L("Małe grupy", "Small groups"), L("Tyle osób, ile jedna osoba naprawdę potrafi uczyć. Uczymy w małych grupach, bo inaczej się nie da uczyć.", "As many people as one teacher can really teach. We teach in small groups because there’s no other way to teach.")),
            (L("Twój własny projekt", "Your own project"), L("Nie ma programu kursu. Robisz to, co chcesz, a technikę łapiesz po drodze. Dlatego można zostać na rok i nie powtarzać niczego.", "There’s no set curriculum. You make what you want and pick up technique along the way. That’s why people stay a year without repeating anything.")),
            (L("Piec na miejscu", "A kiln on site"), L("Wypały są częste, a praca nie wyjeżdża z pracowni. Po 3–4 tygodniach ją odbierasz. Nie przepraszamy za to, tyle trwa wypał.", "Firings are frequent and your work never leaves the building. You collect it after 3–4 weeks. We don’t apologise for that. It’s how long firing takes.")),
            (L("Lepienie i koło", "Hand-building and the wheel"), L("Ciekawi Cię toczenie? Jest odpowiedź. A początkujący ma dokąd dojść.", "Curious about throwing? There’s an answer. And a beginner has somewhere to progress to.")),
            (L("Po polsku i po angielsku", "In Polish or in English"), L("Uczymy po angielsku tak samo chętnie jak po polsku. Cała strona działa w obu językach.", "We teach in English as readily as in Polish. The whole site works in both languages.")),
            (L("Nauczyciel z imienia", "A teacher with a name"), L("Zuzanna uczy, a każdy nauczyciel, którego dołącza do zespołu, zostaje kimś z imienia, a nie obsługą.", "Zuzanna teaches, and every teacher she adds stays a named person, not staff.")),
        ])), "")

    incl = section('<div class="two"><h2>%s</h2><div><p>%s</p>%s</div></div>' % (
        L("Nie musisz nic przynosić", "You don’t need to bring anything"),
        L("Wszystko oprócz wypału szkliwa jest w cenie. Zajęcia regularne opłacasz miesięcznie z góry, bez długiego zobowiązania.", "Everything except glaze firing is in the price. Regular classes are paid monthly in advance, with no long commitment."),
        included_block()), "")

    zu = section('<p class="voice">%s</p><p class="sign">%s</p>' % (
        chk(L("Zrobiłam miejsce, jakiego sama szukałam: gdzie można odejść od ekranu i zająć się czymś, czego nie da się przyspieszyć.", "I built the place I wanted to exist: somewhere you can step away from the screen and spend time on something that can’t be rushed.")),
        L("Zuzanna Muraszkiewicz, założycielka pracowni", "Zuzanna Muraszkiewicz, founder of the studio")), "band-cobalt")

    loc = section('<div class="two"><h2>%s</h2><div><p>%s</p><p><a class="btn ghost" href="%s">%s</a></p></div></div>' % (
        L("Do pracowni się chodzi", "You walk to the studio"),
        L("Jesteśmy w Sadybie, przy ul. Jana III Sobieskiego: w niskiej, zielonej, zwyczajnie mieszkalnej dzielnicy, a nie w modnej okolicy. Dla mieszkańców Wilanowa, Sadyby i Zawad to spacer albo dwa–trzy przystanki. Dlatego cotygodniowy rytm da się utrzymać.",
          "We’re in Sadyba, on ul. Jana III Sobieskiego: a low-rise, green, lived-in neighbourhood rather than a trendy quarter. For people in Wilanów, Sadyba and Zawady it’s a walk or two to three stops. That’s why a weekly rhythm survives."),
        url("contact"), L("Jak do nas trafić", "How to find us")), "band-celadon")

    return hero + router + two + facts + incl + reviews_block() + zu + loc + cta_band(
        L("Chodź polepić.", "Come and make something."),
        L("Napisz albo zadzwoń. Odpowiada człowiek.", "Write or call. A person answers."),
        (url("contact", "formularz"), L("Napisz do nas", "Write to us")), (tel_href(), L("Zadzwoń", "Call")))

def p_classes():
    head_ = phead(L("Zajęcia regularne", "Regular classes"), L("Dwie godziny w tygodniu, które należą do Ciebie. Dla dorosłych i młodzieży od 15 lat, na każdym poziomie.", "Two hours a week that belong to you. For adults and teens from 15, at every level."))
    beg = section('<div class="two"><h2>%s</h2><div><p>%s</p><ul><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Zaczynasz od zera? Tak zaczyna większość.", "Starting from zero? Most people do."),
        L("Nie musisz nic umieć ani nic kupować. Glinę, narzędzia i fartuch masz na miejscu, a początkujący to u nas norma, a nie wyjątek.", "You don’t need to know anything or buy anything. Clay, tools and an apron are here, and beginners are the norm, not the exception."),
        L("Nic nie przynosisz.", "You bring nothing."),
        L("Płacisz miesięcznie z góry. Możesz przestać bez zobowiązań długoterminowych.", "You pay monthly in advance. You can stop; there’s no long commitment."),
        L("Robisz własny projekt, a nie ćwiczenia z programu.", "You work on your own project, not exercises from a syllabus.")), "")
    grafik = '<section class="section band-celadon" id="grafik"><div class="wrap"><h2>%s</h2><p>%s</p>%s</div></section>' % (
        L("Grafik", "Timetable"),
        L("Zajęcia trwają dwie godziny i odbywają się co tydzień albo co dwa tygodnie. Znajdź dzień, który mieści się w Twoim tygodniu.", "Classes last two hours and run weekly or fortnightly. Find the day that fits your week."),
        timetable(["adult"]))
    how = section('<div class="two"><h2>%s</h2><div>%s</div></div>' % (
        L("Jak to działa", "How it works"),
        '<ol class="steps"><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li></ol>' % (
            L("Napisz, która grupa Ci pasuje", "Tell us which group suits you"), L("Albo zadzwoń. Odpowiemy ciepło i bez pośpiechu.", "Or call. We’ll answer warmly and unhurried."),
            L("Płacisz za pierwszy miesiąc", "You pay for the first month"), L("Z góry, przelewem.", "In advance, by bank transfer."),
            L("Przychodzisz na pierwsze zajęcia", "You come to your first class"), L("Przez pierwsze dziesięć minut jest niezręcznie. Potem już nie.", "The first ten minutes are awkward. After that they aren’t."),
            L("Po 3–4 tygodniach odbierasz pracę", "After 3–4 weeks you collect your piece"), L("Wypaloną i gotową. To najlepszy moment.", "Fired and finished. It’s the best moment."))), "")
    miss = section('<div class="two"><h2>%s</h2><div><p>%s</p><p><a href="%s">%s</a></p></div></div>' % (
        L("Nie możesz przyjść w tym tygodniu?", "Can’t make your slot this week?"),
        chk(L("Odrobisz zajęcia w innej grupie w tym samym tygodniu. Daj nam znać wcześniej, a znajdziemy miejsce.", "You can make the class up in another group the same week. Let us know beforehand and we’ll find a place.")),
        url("prices", "nieobecnosci"), L("Pełne zasady", "Full rules")), "band-celadon")
    price_ = section('<div class="two"><h2>%s</h2><div><p><span class="price">%s</span></p><p>%s</p></div></div>' % (
        L("Ile to kosztuje", "What it costs"), price("PRICE_ADULT", L("cena miesięczna", "monthly price")),
        L("Płatność miesięczna z góry. W cenie wszystko poza wypałem szkliwa.", "Paid monthly in advance. Everything is included except glaze firing.")), "")
    return head_ + beg + grafik + how + miss + price_ + section(form_join(), "") + reviews_block()

def p_kids():
    head_ = phead(L("Zajęcia dla dzieci", "Classes for children"), L("Dla dzieci od 7 do 14 lat. Godzina tygodniowo, mała grupa i nauczyciel, który pokazuje, a nie tylko pilnuje.", "For children aged 7 to 14. One hour a week, a small group and a teacher who teaches, not just supervises."))
    top = ('<section class="section"><div class="wrap"><div class="two"><h2>%s</h2><div><p>%s</p><p class="bigline"><a href="%s">%s</a></p><p>%s</p></div></div></div></section>') % (
        L("Wolisz zadzwonić?", "Rather call?"),
        L("Większość rodziców załatwia to jedną rozmową. Zapytaj o wolne miejsca, godziny i o to, kto uczy.", "Most parents settle it in one phone call. Ask about free places, hours and who teaches."),
        tel_href(), tel_text(),
        L("Możesz też napisać formularzem na dole strony.", "You can also use the form further down the page."))
    teacher = section('<div class="two"><h2>%s</h2><div><p>%s</p><p>%s</p></div></div>' % (
        L("Kto uczy", "Who teaches"),
        chk(L("Zajęcia dla dzieci prowadzi %s.", "The children’s classes are taught by %s.") % fill(L("imię", "name"), C["KIDS_TEACHER"])),
        L("W sali jest prawdziwy nauczyciel, nie opiekun. Grupa ma tyle dzieci, ile jedna osoba potrafi uczyć.", "There’s a real teacher in the room, not a minder. The group is as large as one person can teach.")), "band-celadon")
    grafik = '<section class="section" id="grafik"><div class="wrap"><h2>%s</h2><p>%s</p>%s</div></section>' % (
        L("Grupy i godziny", "Groups and hours"),
        L("Zajęcia trwają godzinę, a godziny są podane od początku do końca, żeby łatwo sprawdzić, czy mieszczą się między szkołą a resztą tygodnia.", "Classes last one hour and the times are shown start to finish, so you can check they fit between school and the rest of the week."),
        timetable(["kids7", "kids11"]))
    prog = section('<div class="two"><h2>%s</h2><div><p>%s</p><div class="progress"><figure><div class="pic">%s</div><figcaption>%s<small>%s</small></figcaption></figure><figure><div class="pic">%s</div><figcaption>%s<small>%s</small></figcaption></figure></div><p><small>%s</small></p></div></div>' % (
        L("Co dziecko robi po trzech miesiącach", "What a child makes after three months"),
        L("Płacisz za postępy, a nie za godzinę opieki. Dziecko robi własne rzeczy, a technika przychodzi przy okazji: od pierwszej ściśniętej miseczki do kubka z uchem i szkliwem.", "You’re paying for progress, not for an hour of supervision. Your child makes their own things and technique comes along the way: from a first pinched bowl to a mug with a handle and glaze."),
        pinch_pot_svg(), L("Pierwsze zajęcia", "First session"), L("miseczka ze ściskanej gliny", "a pinched bowl"),
        cup_svg(), L("Po trzech miesiącach", "After three months"), L("kubek z uchem i szkliwem", "a mug with a handle and glaze"),
        chk(L("Ilustracje poglądowe. Warto zastąpić je zdjęciami prac dzieci (za zgodą rodziców).", "Illustrations only. Replace them with photos of children’s work (with parents’ consent)."))), "band-celadon")
    prac = section('<div class="two"><h2>%s</h2><div><ul><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Po prostu praktycznie", "The practical bit"),
        L("Pracownia jest w Sadybie, więc odprowadzenie i odbiór mieszczą się wokół szkoły.", "The studio is in Sadyba, so drop-off and pick-up fit around school."),
        chk(L("Grupy startują wraz z rokiem szkolnym i drugim semestrem. Pytaj o wolne miejsca także w trakcie.", "Groups start with the school year and the second semester. Ask about free places at other times, too.")),
        chk(L("Po zajęciach powiemy Ci, nad czym pracowało dziecko i co zrobi dalej.", "After class we’ll tell you what your child worked on and what comes next.")),
        L("Płatność miesięczna z góry: %s.", "Paid monthly in advance: %s.") % price("PRICE_KIDS", L("cena miesięczna", "monthly price"))), "")
    return head_ + top + teacher + grafik + prog + prac + section(form_kids(), "band-celadon")

def p_workshops():
    head_ = phead(L("Warsztat ceramiczny", "A pottery workshop"), L("Dla jednej osoby, pary albo grupy do ośmiu osób. Około 3,5 godziny, bez doświadczenia.", "For one person, a couple or a group of up to eight. About 3.5 hours, no experience needed."))
    group = section('<div class="two"><h2>%s</h2><div><p>%s</p><p>%s</p></div></div>' % (
        L("Przyjdźcie w trzy, cztery osoby", "Come as three or four"),
        L("Grupa przyjaciół to u nas zwykła rezerwacja. Nie dołączasz do cudzych zajęć. Sala jest wasza na czas warsztatu.", "A group of friends is a normal booking here. You don’t join somebody else’s class. The room is yours for the workshop."),
        L("Urodziny, wieczór panieński, Dzień Kobiet, kolacja, która od dawna się odkłada. Nie musicie nic umieć. Zaczynamy od glinki, a nie od teorii.", "Birthdays, a bachelorette party, Women’s Day, a catch-up that keeps getting postponed. You don’t need to know anything. We start with clay, not theory.")), "")
    dates, sample = free_dates()
    chips = "".join('<button type="button" class="chip" data-date="%s" aria-pressed="false">%s</button>' % (esc(d), ('<mark class="fill">%s</mark>' % d) if (sample and C["REVIEW_MARKS"]) else d) for d in dates)
    free = section('<div class="two"><h2>%s</h2><div><p>%s</p><div class="dates">%s</div><p><small>%s</small></p></div></div>' % (
        L("Najbliższe wolne terminy", "Next free dates"),
        L("Kliknij terminy, które pasują, a trafią do formularza. Wróć do znajomych z dwiema–trzema opcjami zamiast zaczynać od nowa.", "Tap the dates that suit you and they go into the form. Go back to your friends with two or three options instead of starting over."),
        chips, L("Nie ma tu Twojego terminu? Wpisz własny, a sprawdzimy.", "Your date isn’t here? Type your own and we’ll check.")), "band-celadon")
    what = section('<div class="two"><h2>%s</h2><div><ul><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ul>%s</div></div>' % (
        L("Co się dzieje i co zabierasz", "What happens and what you take home"),
        L("Około 3,5 godziny. Ktoś z nas pokazuje technikę, a potem lepicie, co chcecie.", "About 3.5 hours. One of us shows the technique, then you make what you like."),
        L("Każdy robi własną pracę. Po 3–4 tygodniach jest wypalona i gotowa do odbioru.", "Everyone makes their own piece. After 3–4 weeks it’s fired and ready to collect."),
        chk(L("Jedna osoba może odebrać prace dla całej grupy.", "One person can collect the pieces for the whole group.")),
        L("Cena za osobę: %s.", "Price per person: %s.") % price("PRICE_WORKSHOP", L("cena za osobę", "price per person")),
        included_block()), "")
    resched = section('<div class="two"><h2>%s</h2><div><p>%s</p></div></div>' % (
        L("Co jeśli ktoś nie może przyjść", "What if someone can’t make it"),
        chk(L("Jeśli ktoś z grupy nie może w uzgodniony dzień, przesuwamy termin dla wszystkich lub zmieniamy liczbę osób. Dajcie znać najpóźniej na kilka dni przed.", "If someone in your group can’t make the agreed day we move the date for everyone or change the number of people. Tell us a few days beforehand."))), "band-celadon")
    return head_ + group + free + what + resched + section(form_group(), "") + reviews_block()

def p_voucher():
    head_ = phead(L("Bon na warsztat", "A workshop voucher"), L("Prezent, który nie wygląda jak każdy inny. Kupujesz Ty, a termin wybiera obdarowany.", "A present that doesn’t look like every other present. You buy it; the recipient picks the date."))
    urgent = ('<section class="section" style="padding-bottom:0"><div class="wrap"><div class="urgent"><h2>%s</h2><p>%s</p><p><a class="btn light big" href="%s">%s %s</a></p></div></div></section>') % (
        L("Prezent za trzy dni?", "Present due in three days?"),
        chk(L("Zadzwoń. Bon w wersji PDF dostajesz mailem zaraz po potwierdzeniu płatności, a drukowany odbierasz w pracowni.", "Call us. The PDF voucher reaches you by email right after payment is confirmed, and you can collect a printed copy at the studio.")),
        tel_href(), L("Zadzwoń:", "Call:"), re_strip(tel_text()))
    v = ('<section class="section"><div class="wrap"><div class="two"><div class="voucher">%s<p class="v-kicker">%s</p><p class="v-title">%s</p><p>%s</p><p>%s</p><p class="v-foot">Studio Piegus · Sadyba, Warszawa</p></div>'
         '<div><h2>%s</h2><p>%s</p></div></div></div></section>') % (
        dots_svg(), L("Bon na warsztat ceramiczny", "A pottery workshop voucher"), L("Dla Ciebie.", "For you."),
        L("Warsztat ceramiczny w Studio Piegus: około 3,5 godziny, bez żadnego doświadczenia. Glina i fartuch czekają na miejscu.", "A pottery workshop at Studio Piegus: about 3.5 hours, no experience at all. Clay and an apron are waiting."),
        L("Termin wybierasz Ty. Masz na to pół roku.", "You choose the date. You have six months."),
        L("Tak wygląda bon", "This is what the voucher looks like"),
        L("Jest napisany do osoby obdarowanej, a nie do kupującego: mówi, co się będzie działo, i że nie trzeba nic umieć. Dostajesz go jako PDF albo w wersji drukowanej.", "It’s written to the person receiving it, not the buyer: it says what will happen and that no experience is needed. You get it as a PDF or a printed copy."))
    answers = section('<div class="two"><h2>%s</h2><div><p>%s</p><ul><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Co odpowiesz, gdy ktoś zacznie pytać", "What to say when they start asking"),
        L("W kilku zdaniach, żeby nie trzeba było niczego udawać:", "In a few lines, so you don’t have to pretend:"),
        L("To około 3,5 godziny w małej grupie albo we dwoje.", "It’s about 3.5 hours, in a small group or as a pair."),
        L("Obdarowany robi własną rzecz z gliny i po 3–4 tygodniach odbiera ją wypaloną.", "The recipient makes their own piece from clay and collects it fired 3–4 weeks later."),
        L("Nie trzeba nic umieć.", "No experience is needed."),
        L("Termin wybiera sam, w ciągu pół roku od zakupu.", "They choose their own date within six months of purchase.")), "band-celadon")
    opts = section('<h2>%s</h2><ul class="facts">%s</ul>' % (
        L("Co możesz kupić", "What you can buy"),
        "".join('<li><h3>%s</h3><p>%s</p><p class="price">%s</p></li>' % x for x in [
            (L("Bon dla jednej osoby", "One person"), L("Warsztat ceramiczny, około 3,5 godziny.", "A pottery workshop, about 3.5 hours."), price("PRICE_VOUCHER_1", L("cena", "price"))),
            (L("Bon dla dwóch osób", "Two people"), L("Idźcie razem. To czas spędzony we dwoje, a nie kolejna kolacja.", "Go together. It’s time spent as a pair rather than another dinner."), price("PRICE_VOUCHER_2", L("cena", "price"))),
            (L("Bon na serię zajęć", "A run of classes"), L("Dla kogoś, kto wie, że chce zostać na dłużej. Zapytaj o szczegóły.", "For someone who knows they want to stay. Ask for details."), L("Wycena po rozmowie", "Priced after a call")),
        ])), "")
    deliver = section('<div class="two"><h2>%s</h2><div><ul><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Jak bon do Ciebie trafia", "How the voucher reaches you"),
        chk(L("PDF na e-mail po potwierdzeniu płatności, nawet w ostatniej chwili.", "A PDF by email once payment is confirmed, even at the last minute.")),
        chk(L("Wersja drukowana do odbioru w pracowni.", "A printed copy to collect at the studio.")),
        L("Płacisz przelewem. Pilne? Zadzwoń, a ustalimy, jak zdążyć.", "You pay by bank transfer. In a hurry? Call and we’ll work out how to make it in time.")), "")
    return head_ + urgent + v + answers + opts + deliver + section(form_voucher(), "band-celadon") + reviews_block()

def re_strip(s): return s

def p_teams():
    head_ = phead(L("Integracja bez slajdów", "Team-building without the slides"), L("Przyjeżdżamy do Was albo zapraszamy do pracowni. Każdy wychodzi z czymś, co sam zrobił.", "We come to your office, or you come to us. Everyone leaves with something they made."))
    sceptic = section('<div class="two"><h2>%s</h2><div><p>%s</p><p>%s</p></div></div>' % (
        L("Przetrwa dwie osoby, które narzekają na wszystko", "It survives the two people who complain about everything"),
        L("Nie trzeba nic umieć, a nikt nie występuje przed nikim. Każdy ma coś w rękach i coś do zrobienia, więc nie ma kogo zostawić z boku.", "Nobody needs experience and nobody performs for anyone. Everyone has something in their hands and something to do, so nobody is left on the side."),
        L("Zespół może robić własne rzeczy albo budować wspólny obiekt. Ustalamy to z Tobą.", "The team can each make their own piece or build one object together. We agree that with you.")), "")
    logi = section('<div class="two"><h2>%s</h2><div><ul><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Logistyka na naszej głowie", "Logistics are on us"),
        L("Prowadzimy warsztat w Waszym biurze albo w pracowni w Sadybie. Większość pracowni robi tylko jedno z dwojga.", "We run the workshop at your office or at the studio in Sadyba. Most studios do only one of the two."),
        L("Zapewniamy glinę, narzędzia, fartuchy i wypał.", "We bring clay, tools, aprons and firing."),
        chk(L("Wypalone prace odbieracie po 3–4 tygodniach: w pracowni albo ustalamy dostawę do biura.", "You get the fired pieces after 3–4 weeks: collect them at the studio or we arrange delivery to your office."))), "band-celadon")
    scen = section('<div class="two"><h2>%s</h2><div><p>%s</p><ol class="steps"><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li></ol><p><small>%s</small></p></div></div>' % (
        L("Przykładowy scenariusz", "A sample scenario"),
        L("Poniżej wersja na około 3,5 godziny. Dopasowujemy ją do Waszego zespołu i dnia.", "Below is a version of about 3.5 hours. We adapt it to your team and your day."),
        L("Powitanie i pokaz", "Welcome and demonstration"), chk(L("Około 30 minut: fartuchy, pierwsze ruchy w glinie, krótki pokaz.", "About 30 minutes: aprons, first moves in clay, a short demonstration.")),
        L("Lepienie", "Making"), chk(L("Około 2,5 godziny: każdy robi własną pracę albo zespół buduje wspólną.", "About 2.5 hours: everyone makes their own piece, or the team builds one together.")),
        L("Zakończenie", "Wrap-up"), chk(L("Około 30 minut: porządki, zdjęcia, rozmowa o tym, co kto zrobił.", "About 30 minutes: tidying, photos, talking about what everyone made.")),
        L("Wypał i odbiór", "Firing and collection"), chk(L("Po 3–4 tygodniach: prace wracają do zespołu.", "After 3–4 weeks: the pieces go back to the team.")),
        L("Czas, liczba osób i miejsce zmieniają plan. Dostaniesz gotową propozycję.", "Time, group size and place change the plan. You will get a finished proposal.")), "")
    docs = section('<div class="two"><h2>%s</h2><div><p>%s</p><ul><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ul></div></div>' % (
        L("Coś, co możesz przekazać dyrektorowi", "Something you can pass to your director"),
        L("Odpowiadamy gotową propozycją, a nie listą pytań. Bez przepisywania:", "We answer with a finished proposal, not a list of questions. No rewriting:"),
        L("scenariusz i harmonogram", "the scenario and the timings"),
        L("zakres: co jest w cenie", "what the price includes"),
        L("jedna cena całkowita (wycena indywidualna)", "one total price (quoted individually)"),
        L("oferta na piśmie i faktura", "a written quote and a proper invoice")), "band-celadon")
    proc = section('<div class="two"><h2>%s</h2><div><ol class="steps"><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li><li><div><strong>%s</strong>%s</div></li></ol></div></div>' % (
        L("Jak to wygląda", "How it works"),
        L("Piszesz", "You write"), L("Liczba osób, termin, miejsce. Nic więcej.", "Headcount, date, place. Nothing more."),
        L("Dostajesz propozycję", "You get a proposal"), chk(L("W ciągu jednego dnia roboczego, na piśmie.", "Within one working day, in writing.")),
        L("Dyrektor akceptuje", "Your director approves"), L("Ustalamy szczegóły mailem, wszystko ma pisemny ślad.", "We settle the details by email; everything is in writing."),
        L("Warsztat", "The workshop"), L("Potem faktura, a prace wracają po wypale.", "Then the invoice, and the pieces return after firing.")), "")
    return head_ + sceptic + logi + scen + docs + proc + section(form_team(), "band-celadon") + reviews_block()

def p_prices():
    head_ = phead(L("Ceny i zasady", "Prices and rules"), L("Co jest w cenie, co kosztuje dodatkowo i co z nieobecnościami. Wszystko w jednym miejscu.", "What’s included, what costs extra and what happens if you miss a class. All in one place."))
    tbl = ('<table class="pricelist"><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>'
           '<tr><th>%s</th><td>%s<small>%s</small></td><td>%s</td></tr>'
           '<tr><th>%s</th><td>%s<small>%s</small></td><td>%s</td></tr>'
           '<tr><th>%s</th><td>%s<small>%s</small></td><td>%s</td></tr>'
           '<tr><th>%s</th><td>%s<small>%s</small></td><td>%s</td></tr>'
           '<tr><th>%s</th><td>%s</td><td>%s</td></tr>'
           '<tr><th>%s</th><td>%s</td><td>%s</td></tr></tbody></table>') % (
        L("Co", "What"), L("Cena", "Price"), L("Jak płacisz", "How you pay"),
        L("Zajęcia dorośli i młodzież 15+", "Adults and teens 15+"), '<span class="price">%s</span>' % price("PRICE_ADULT", L("cena", "price")), L("2 godziny, co tydzień lub co dwa tygodnie", "2 hours, weekly or fortnightly"), L("Miesięcznie z góry", "Monthly, in advance"),
        L("Zajęcia dla dzieci 7–14", "Children 7–14"), '<span class="price">%s</span>' % price("PRICE_KIDS", L("cena", "price")), L("1 godzina, co tydzień lub co dwa tygodnie", "1 hour, weekly or fortnightly"), L("Miesięcznie z góry", "Monthly, in advance"),
        L("Warsztat, za osobę", "Workshop, per person"), '<span class="price">%s</span>' % price("PRICE_WORKSHOP", L("cena", "price")), L("ok. 3,5 godziny, 1–8 osób", "about 3.5 hours, 1–8 people"), L("Przelewem przed warsztatem", "Bank transfer before the workshop"),
        L("Bon", "Voucher"), '<span class="price">%s</span> / <span class="price">%s</span>' % (price("PRICE_VOUCHER_1", L("1 os.", "1 person")), price("PRICE_VOUCHER_2", L("2 os.", "2 people"))), L("Ważny 6 miesięcy; obdarowany wybiera termin", "Valid 6 months; the recipient picks the date"), L("Przelewem", "Bank transfer"),
        L("Wypał szkliwa", "Glaze firing"), '<span class="price">%s</span>' % price("PRICE_GLAZE", L("cena", "price")), L("Przy odbiorze pracy", "When you collect your piece"),
        L("Warsztat dla firm", "Team workshop"), L("Wycena indywidualna", "Quoted individually"), L("Oferta na piśmie, faktura", "Written quote, invoice"))
    main = section('<h2>%s</h2>%s%s' % (L("Cennik", "Price list"), tbl, included_block()), "")
    rules = section('<div class="two" id="nieobecnosci"><h2>%s</h2><div><h3>%s</h3><p>%s</p><h3>%s</h3><p>%s</p><h3>%s</h3><p>%s</p><h3>%s</h3><p>%s</p></div></div>' % (
        L("Zasady", "Rules"),
        L("Nieobecność na zajęciach", "Missing a class"), chk(L("Daj znać wcześniej, a odrobisz zajęcia w innej grupie w tym samym tygodniu.", "Let us know beforehand and you can make the class up in another group the same week.")),
        L("Warsztat dla grupy", "Group workshops"), chk(L("Jeśli ktoś nie może przyjść, przesuwamy termin dla wszystkich albo zmieniamy liczbę osób. Dajcie znać kilka dni wcześniej.", "If someone can’t come we move the date for everyone or change the number of people. Tell us a few days ahead.")),
        L("Bon", "Vouchers"), L("Bon jest ważny pół roku od zakupu. Obdarowany wybiera termin sam.", "A voucher is valid for six months from purchase. The recipient chooses their own date."),
        L("Odbiór pracy", "Collecting your piece"), L("Praca jest gotowa po 3–4 tygodniach od zajęć. Tyle trwa wypał.", "Your piece is ready 3–4 weeks after class. That’s how long firing takes.")), "band-celadon")
    faq = section('<h2>%s</h2><div class="faq">%s</div>' % (L("Częste pytania", "Questions we get a lot"), "".join(
        '<details><summary>%s</summary><p>%s</p></details>' % x for x in [
            (L("Czy muszę coś przynieść?", "Do I need to bring anything?"), L("Nie. Glina, szkliwa, narzędzia i fartuch są na miejscu.", "No. Clay, glazes, tools and an apron are here.")),
            (L("Czy muszę zapisywać się na długo?", "Do I have to commit for long?"), L("Nie. Płacisz za miesiąc z góry, bez długiego zobowiązania.", "No. You pay for a month in advance, with no long commitment.")),
            (L("Czy muszę mieć doświadczenie?", "Do I need any experience?"), L("Nie. Początkujący to u nas norma. Nie musisz nic umieć.", "No. Beginners are the norm here. You don’t need to know anything.")),
            (L("Dlaczego na pracę czeka się 3–4 tygodnie?", "Why does the wait for my piece take 3–4 weeks?"), L("Tyle trwa wypał. Piec mamy na miejscu, więc czekasz krócej niż w pracowniach, które wysyłają prace gdzie indziej.", "That’s how long firing takes. The kiln is on site, so the wait is shorter than at studios that send work elsewhere.")),
            (L("Czy uczycie po angielsku?", "Do you teach in English?"), L("Tak, tak samo chętnie jak po polsku.", "Yes, as readily as in Polish.")),
            (L("Czy mogę przyjść z kimś?", "Can I bring someone?"), L("Tak. Warsztat jest dla 1–8 osób, a na zajęciach regularnych zapytaj o wolne miejsce.", "Yes. A workshop is for 1–8 people, and for regular classes just ask about a free place.")),
        ])), "")
    return head_ + main + rules + faq + cta_band(L("Nie ma tu Twojego pytania?", "Your question isn’t here?"), L("Zapytaj. Odpowiada człowiek.", "Ask. A person answers."), (url("contact", "formularz"), L("Napisz do nas", "Write to us")), (tel_href(), L("Zadzwoń", "Call")))

def p_members():
    head_ = phead(L("Dla uczestników", "For participants"), L("Odpowiedzi na pytania, które wracają. Żeby nie trzeba było pytać za każdym razem.", "Answers to the questions that come back. So you don’t have to ask every time."))
    blocks = [
        (L("Nie możesz przyjść w swoim terminie", "Can’t make your usual slot"), '<p>%s</p><p><a class="btn ghost" href="%s">%s</a></p>' % (chk(L("Odrobisz zajęcia w innej grupie w tym samym tygodniu. Zobacz, co działa, i daj nam znać wcześniej.", "You can make the class up in another group the same week. See what’s running and let us know beforehand.")), url("classes", "grafik"), L("Zobacz grafik", "See the timetable"))),
        (L("Odbiór pracy", "Collecting your piece"), '<p>%s</p><p>%s</p>' % (L("Praca jest gotowa po 3–4 tygodniach od zajęć. To jest moment, na który się czeka: przyjdź, odbierz i obejrzyj.", "Your piece is ready 3–4 weeks after class. It’s the moment you wait for: come, collect, take a look."), chk(L("Napiszemy do Ciebie, gdy praca będzie gotowa do odbioru.", "We’ll write to you when your piece is ready to collect.")))),
        (L("Wypał szkliwa", "Glaze firing"), '<p>%s</p>' % (L("Wypał szkliwa jest poza ceną zajęć i płacisz go przy odbiorze: %s. Weź przelew albo gotówkę.", "Glaze firing isn’t part of the class price and you pay it when you collect: %s. Bring a transfer or cash.") % price("PRICE_GLAZE", L("cena wypału", "glaze firing price")))),
        (L("Płatności", "Payments"), '<p>%s</p>' % L("Zajęcia opłacasz miesięcznie z góry przelewem. Dane do przelewu dostajesz w wiadomości na początku.", "You pay for classes monthly in advance by bank transfer. The details are in the message you received at the start.")),
        (L("Kontynuacja i przerwa", "Continuing and pausing"), '<p>%s</p>' % chk(L("Pod koniec semestru zapytamy, nad czym chcesz pracować dalej. Jeśli chcesz zrobić przerwę, napisz przed początkiem kolejnego miesiąca.", "At the end of the term we’ll ask what you’d like to work on next. If you want a break, write before the next month begins."))),
    ]
    body = section('<div class="faq">%s</div>' % "".join('<details open><summary>%s</summary>%s</details>' % b for b in blocks), "")
    return head_ + body + cta_band(L("Coś jeszcze?", "Anything else?"), L("Napisz albo zadzwoń.", "Write or call."), (url("contact", "formularz"), L("Napisz do nas", "Write to us")), (tel_href(), L("Zadzwoń", "Call")))

def p_contact():
    head_ = phead(L("Kontakt i dojazd", "Contact and directions"), L("Odpowiadamy sami, ludzie, a nie automaty. Zadzwoń, jeśli wolisz porozmawiać.", "We answer ourselves, people rather than bots. Call if you’d rather talk."))
    left = ('<div><p class="bigline"><a href="%s">%s</a></p><p class="bigline"><a href="%s">%s</a></p>'
            '<p>%s</p><h3>%s</h3><p>ul. Jana III Sobieskiego %s<br>Sadyba, Warszawa</p><p><a href="%s" rel="noopener">%s</a></p>'
            '<p>%s</p><div class="map"><iframe title="%s" src="%s" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div></div>') % (
        tel_href(), tel_text(), mail_href(), mail_text(),
        chk(L("Telefon odbieramy w godzinach: %s.", "We answer the phone during: %s.") % fill(L("godziny", "hours"))),
        L("Pracownia", "The studio"), fill(L("nr", "no."), C["STREET_NO"]), MAPS_LINK, L("Otwórz w Mapach Google", "Open in Google Maps"),
        L("Z Wilanowa, Sadyby i Zawad dojdziesz pieszo albo dojedziesz dwa–trzy przystanki. Uczymy po polsku i po angielsku.", "From Wilanów, Sadyba and Zawady you can walk or ride two to three stops. We teach in Polish and in English."),
        L("Mapa dojazdu", "Map"), MAPS_EMBED)
    soc = ""
    if C["INSTAGRAM"] or C["FACEBOOK"]:
        soc = '<p>%s</p>' % " · ".join(x for x in ['<a href="%s" rel="noopener">Instagram</a>' % esc(C["INSTAGRAM"]) if C["INSTAGRAM"] else "", '<a href="%s" rel="noopener">Messenger / Facebook</a>' % esc(C["FACEBOOK"]) if C["FACEBOOK"] else ""] if x)
    return head_ + section('<div class="contact-grid">%s<div>%s%s</div></div>' % (left, form_contact(), soc), "")

# ───────────────────────────── Pliki statyczne ─────────────────────────────
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(text)

def build():
    global LANG
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    shutil.copy(os.path.join(SRC, "style.css"), os.path.join(OUT, "assets", "style.css"))
    shutil.copy(os.path.join(SRC, "site.js"), os.path.join(OUT, "assets", "site.js"))
    # Piegi — tekstura
    for name, color in (("speckle-light.svg", "#6B3F26"), ("speckle-dark.svg", "#F6F5F1")):
        dots = speckle_dots(11 if "light" in name else 12, 52, 380, 380, [color], .7, 2.2)
        write(os.path.join(OUT, "assets", name), '<svg xmlns="http://www.w3.org/2000/svg" width="380" height="380" viewBox="0 0 380 380" opacity="%s">%s</svg>' % (".16" if "light" in name else ".22", dots))
    write(os.path.join(OUT, "assets", "favicon.svg"), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#2B4BA0"/>%s</svg>' % speckle_dots(2, 12, 64, 64, ["#F6F5F1"], 1.4, 3))
    fn = dict(home=p_home, classes=p_classes, kids=p_kids, workshops=p_workshops, voucher=p_voucher, teams=p_teams, prices=p_prices, members=p_members, contact=p_contact)
    urls = []
    for lang in ("pl", "en"):
        LANG = lang
        for key in PAGES:
            out = os.path.join(OUT, "" if lang == "pl" else "en", slug(key, lang))
            write(out, page(key, fn[key]()))
            urls.append(abs_url(key, lang))
    write(os.path.join(OUT, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join("  <url><loc>%s</loc></url>" % u for u in urls))
    write(os.path.join(OUT, "robots.txt"), "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % C["DOMAIN"])
    print("Zbudowano %d stron w %s" % (len(urls), OUT))

if __name__ == "__main__":
    build()
