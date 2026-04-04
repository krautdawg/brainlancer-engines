"""Pre-loaded demo campaign: 5 German B2B leads with fully generated 4-email sequences."""

DEMO_CAMPAIGN = {
    "name": "Demo: KI Katapult Outreach Q2",
    "sender_name": "Max Müller",
    "sender_email": "max.mueller@kikatapult.de",
    "num_touchpoints": 4,
    "cadence": "1,3,7,14",
    "tone": "formal",
    "goal": "meeting",
    "status": "active",
    "is_demo": True,
}

DEMO_LEADS = [
    {
        "company": "TechMed GmbH",
        "contact": "Dr. Sarah Weber",
        "email": "s.weber@techmed-gmbh.de",
        "website": "https://techmed-gmbh.de",
        "notes": "Healthcare tech, 50–200 employees, expanding into AI diagnostics",
        "status": "draft",
    },
    {
        "company": "Logistik Pro AG",
        "contact": "Thomas Bauer",
        "email": "t.bauer@logistik-pro.de",
        "website": "https://logistik-pro.de",
        "notes": "Logistics company, 200–500 employees, route optimisation challenges",
        "status": "sent",
    },
    {
        "company": "FinanzWerk Beratung",
        "contact": "Claudia Hoffmann",
        "email": "c.hoffmann@finanzwerk.de",
        "website": "https://finanzwerk.de",
        "notes": "Financial consulting, 10–50 employees, process automation interest",
        "status": "replied",
    },
    {
        "company": "BauTech Solutions",
        "contact": "Andreas Schröder",
        "email": "a.schroeder@bautech-solutions.de",
        "website": "https://bautech-solutions.de",
        "notes": "Construction tech startup, 10–50 employees, new product launch",
        "status": "draft",
    },
    {
        "company": "Retail Innovation KG",
        "contact": "Julia Zimmermann",
        "email": "j.zimmermann@retail-innovation.de",
        "website": "https://retail-innovation.de",
        "notes": "Retail tech, 50–200 employees, looking to improve customer analytics",
        "status": "meeting_booked",
    },
]

# Pre-generated sequences keyed by company name
DEMO_SEQUENCES = {
    "TechMed GmbH": [
        {
            "touchpoint_num": 1, "scheduled_day": 1,
            "subject": "KI-Diagnostik bei TechMed – ein Gedanke",
            "body": "Sehr geehrte Frau Dr. Weber,\n\nals ich mir die Entwicklungen bei TechMed GmbH angesehen habe, ist mir sofort aufgefallen, wie strategisch Ihr Fokus auf KI-gestützte Diagnostik ausgerichtet ist.\n\nGenau hier setzt unsere Arbeit bei KI Katapult an: Wir helfen Unternehmen wie Ihrem, KI-Initiativen schnell vom Konzept in die Praxis zu bringen – ohne monatelange Einführungsphasen.\n\nFür einen Healthcare-Tech-Anbieter wie TechMed bedeutet das konkret: schnellere Validierung von Diagnose-Algorithmen, bessere Integration bestehender Systeme und messbare Ergebnisse innerhalb von Wochen.\n\nDarf ich Ihnen in einem 20-minütigen Gespräch zeigen, wie wir das für ähnliche Unternehmen umgesetzt haben?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 2, "scheduled_day": 3,
            "subject": "Wie Meditec ihre KI-Einführung um 60 % beschleunigt hat",
            "body": "Sehr geehrte Frau Dr. Weber,\n\nnur kurz zur Erinnerung – und weil ich dachte, das könnte Sie interessieren:\n\nEin ähnliches Unternehmen wie TechMed – Meditec aus München – stand vor 8 Monaten vor der gleichen Herausforderung: exzellente KI-Ideen, aber zu langsame Umsetzung.\n\nNach unserer Zusammenarbeit konnten sie:\n- Ihren ersten KI-Prototypen in 6 Wochen statt 6 Monaten launchen\n- Die Fehlerrate in der Bildanalyse um 34 % reduzieren\n- Zwei neue Produktlinien auf Basis der Erkenntnisse entwickeln\n\nIch wäre gespannt, ob ähnliche Ergebnisse auch für TechMed realistisch wären.\n\nHaben Sie 20 Minuten diese Woche?\n\nViele Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 3, "scheduled_day": 7,
            "subject": "Die eine Frage, die KI-Projekte scheitern lässt",
            "body": "Sehr geehrte Frau Dr. Weber,\n\nin Gesprächen mit Healthcare-Tech-Unternehmen höre ich immer wieder dasselbe: Die Technologie ist bereit, aber die Organisation hinkt hinterher.\n\nDas klingt vielleicht vertraut. Und genau das kostet Unternehmen wie TechMed Monate – manchmal sogar Jahre.\n\nBei KI Katapult haben wir einen Ansatz entwickelt, der genau an diesem Punkt ansetzt: Wir sorgen dafür, dass KI-Projekte nicht nur technisch funktionieren, sondern im Unternehmen tatsächlich leben.\n\nDie Frage ist nicht ob KI bei TechMed eine Rolle spielen wird – sondern wie schnell.\n\nEin kurzes Gespräch könnte der erste Schritt sein. Wann hätten Sie 20 Minuten?\n\nFreundliche Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 4, "scheduled_day": 14,
            "subject": "Letzter Versuch – soll ich aufhören?",
            "body": "Sehr geehrte Frau Dr. Weber,\n\nich möchte Sie nicht weiter belästigen – daher direkt gefragt:\n\nIst der Zeitpunkt für KI-Themen bei TechMed gerade einfach nicht der richtige?\n\nIch frage, weil ich in der Regel nur dann weitermache, wenn es tatsächlich einen Mehrwert gibt. Wenn das Timing nicht stimmt oder das Thema intern keine Priorität hat, ist das völlig verständlich.\n\nFalls Sie jedoch grundsätzlich Interesse haben, aber einfach keine Zeit hatten zu antworten – ich freue mich über eine kurze Rückmeldung.\n\nUnd falls nicht: Kein Problem. Ich wünsche TechMed weiterhin viel Erfolg.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
    ],
    "Logistik Pro AG": [
        {
            "touchpoint_num": 1, "scheduled_day": 1,
            "subject": "Routenoptimierung bei Logistik Pro – 20 Minuten?",
            "body": "Sehr geehrter Herr Bauer,\n\nin der Logistikbranche hängt Profitabilität oft an einem einzigen Faktor: optimierte Routen.\n\nIch habe gesehen, dass Logistik Pro AG in einem sehr kompetitiven Umfeld operiert. Gleichzeitig wissen wir aus der Praxis: Viele mittelständische Logistiker lassen 15–25 % Effizienz auf der Strecke liegen – einfach weil die richtigen KI-Tools fehlen.\n\nKI Katapult hat mehreren Logistikunternehmen geholfen, ihre Routenplanung durch KI um 20–30 % zu optimieren – bei Einführungszeiten von unter 8 Wochen.\n\nDarf ich Ihnen zeigen, was das konkret für Logistik Pro bedeuten könnte?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 2, "scheduled_day": 3,
            "subject": "Zahlen aus der Praxis: Logistik + KI",
            "body": "Sehr geehrter Herr Bauer,\n\nkurze Nachfrage zu meiner letzten Mail – und ein konkretes Beispiel:\n\nTransLogix, ein mittelständisches Logistikunternehmen mit ähnlicher Struktur wie Logistik Pro, hat mit unserer Unterstützung:\n\n- Leerfahrten um 28 % reduziert\n- Lieferzeiten um durchschnittlich 2,3 Stunden verkürzt\n- Den Treibstoffverbrauch um 18 % gesenkt\n\nDas Ergebnis: ROI innerhalb von 4 Monaten.\n\nSolche Ergebnisse sind kein Zufall – sie entstehen durch den richtigen KI-Ansatz, angepasst auf Ihre Prozesse.\n\nIch würde gerne erfahren, wo Logistik Pro aktuell den größten Optimierungsdruck sieht. Haben Sie 20 Minuten?\n\nViele Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 3, "scheduled_day": 7,
            "subject": "Der versteckte Kostentreiber in der Logistik",
            "body": "Sehr geehrter Herr Bauer,\n\nes gibt einen Kostenfaktor in der Logistik, über den selten gesprochen wird: schlechte Daten.\n\nViele Unternehmen investieren in neue Fahrzeuge oder Software – aber die eigentliche Wertschöpfung liegt in den Daten, die täglich entstehen und ungenutzt bleiben.\n\nBei KI Katapult haben wir einen Ansatz, der genau diese Daten zum Leben erweckt: Predictive Analytics, die Ihnen sagen, wo morgen Engpässe entstehen – bevor sie passieren.\n\nIch glaube, das wäre auch für Logistik Pro relevant. Darf ich Ihnen das in einem kurzen Call vorstellen?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 4, "scheduled_day": 14,
            "subject": "Abschluss meiner Kontaktaufnahme",
            "body": "Sehr geehrter Herr Bauer,\n\nich werde mich nach dieser Mail nicht mehr melden – versprochen.\n\nAber bevor ich das tue: Falls KI-Optimierung für Logistik Pro in den nächsten 12 Monaten ein Thema wird, denken Sie gerne an uns.\n\nWir helfen mittelständischen Logistikunternehmen, messbare Ergebnisse mit KI zu erzielen – schnell, pragmatisch und ohne übertriebene IT-Projekte.\n\nIch wünsche Ihnen und Logistik Pro viel Erfolg.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
    ],
    "FinanzWerk Beratung": [
        {
            "touchpoint_num": 1, "scheduled_day": 1,
            "subject": "Prozessautomatisierung für FinanzWerk – ein Impuls",
            "body": "Sehr geehrte Frau Hoffmann,\n\nin der Finanzberatung läuft eine der größten Transformationen seit Jahren: Firmen, die KI-gestützte Automatisierung früh einsetzen, gewinnen massive Wettbewerbsvorteile.\n\nIch habe FinanzWerk Beratung als ein Unternehmen kennengelernt, das Qualität und Expertise in den Vordergrund stellt. Genau das sind die Firmen, die von smarter Automatisierung am meisten profitieren.\n\nKI Katapult hilft Beratungsunternehmen dabei, repetitive Prozesse zu automatisieren – von der Dokumentenanalyse bis zur Berichtserstellung – damit Ihr Team sich auf das konzentrieren kann, was wirklich zählt.\n\nDarf ich Ihnen in 20 Minuten zeigen, was das konkret bedeuten könnte?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 2, "scheduled_day": 3,
            "subject": "40 Stunden pro Monat zurückgewinnen",
            "body": "Sehr geehrte Frau Hoffmann,\n\neine kurze Nachfrage zu meiner letzten Mail:\n\nEine Boutique-Unternehmensberatung aus Frankfurt – ähnlich strukturiert wie FinanzWerk – hat durch unsere KI-Automatisierung monatlich 40 Stunden Beraterzeit zurückgewonnen.\n\nDie Zeit wird jetzt genutzt für: neue Mandate, tiefere Kundenanalysen und strategische Projekte.\n\nDas war möglich durch drei Automatisierungen:\n1. Automatische Analyse von Finanzdokumenten\n2. KI-gestützte Berichtserstellung\n3. Intelligentes Mandantenmonitoring\n\nIch bin gespannt, ob ähnliches auch für FinanzWerk Sinn machen würde. Haben Sie 20 Minuten?\n\nViele Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 3, "scheduled_day": 7,
            "subject": "Was Ihre Berater wirklich von KI erwarten",
            "body": "Sehr geehrte Frau Hoffmann,\n\nwir beobachten einen interessanten Trend: Die besten Berater fordern heute aktiv KI-Tools ein – weil sie wissen, dass sie damit mehr leisten können.\n\nFür FinanzWerk Beratung bedeutet das: Wer jetzt in smarte Automatisierung investiert, wird bessere Talente anziehen und halten können.\n\nKI Katapult bietet keine Komplettlösungen von der Stange – wir analysieren erst Ihre Prozesse und identifizieren, wo der größte Hebel liegt.\n\nIch glaube, das wäre ein sinnvoller nächster Schritt für FinanzWerk. Wann haben Sie 20 Minuten?\n\nFreundliche Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 4, "scheduled_day": 14,
            "subject": "Letzte Nachricht von mir",
            "body": "Sehr geehrte Frau Hoffmann,\n\ndies ist meine letzte Nachricht an Sie – ich möchte Ihre Zeit respektieren.\n\nFalls KI-Automatisierung für FinanzWerk Beratung in Zukunft ein Thema wird, freue ich mich über Ihre Kontaktaufnahme.\n\nUnd falls Sie grundsätzlich offen für einen kurzen Austausch wären – auch ohne konkrete Absicht – bin ich für ein 15-minütiges Gespräch jederzeit erreichbar.\n\nIch wünsche Ihnen viel Erfolg.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
    ],
    "BauTech Solutions": [
        {
            "touchpoint_num": 1, "scheduled_day": 1,
            "subject": "BauTech Solutions – Ihr neues Produkt und KI",
            "body": "Sehr geehrter Herr Schröder,\n\nein neues Produkt zu launchen ist aufregend – und gleichzeitig eine enorme Herausforderung. Der Druck, schnell Traktion zu gewinnen, ist real.\n\nIch habe BauTech Solutions genauer angesehen und sehe ein Unternehmen mit klarer Vision. Was mich interessiert: Setzen Sie bereits KI ein, um Ihren Markteintritt zu beschleunigen?\n\nKI Katapult hat mehrere Startups und Scale-ups in der Bautech-Branche dabei begleitet, ihre Produkte mit KI-Funktionen anzureichern und schneller Product-Market-Fit zu finden.\n\nEin Gespräch könnte neue Perspektiven öffnen. Haben Sie 20 Minuten?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 2, "scheduled_day": 3,
            "subject": "Wie ConstructAI in 3 Monaten 50 Neukunden gewann",
            "body": "Sehr geehrter Herr Schröder,\n\nkurze Nachfrage – und eine Geschichte, die Sie interessieren könnte:\n\nConstructAI, ein Bautech-Startup aus Hamburg, war in einer ähnlichen Phase wie BauTech Solutions: starkes Produkt, aber schleppender Vertrieb.\n\nWas wir gemeinsam gemacht haben:\n- KI-gestütztes Lead-Scoring zur Priorisierung der besten Prospects\n- Automatisierte Personalisierung der Outreach-Kampagnen\n- Intelligentes CRM-Tracking für Follow-ups\n\nDas Ergebnis: 50 qualifizierte Neukunden in 90 Tagen.\n\nIch glaube, ähnliche Ergebnisse sind auch für BauTech realistisch. Wann hätten Sie 20 Minuten?\n\nViele Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 3, "scheduled_day": 7,
            "subject": "Der Fehler, den die meisten Startups beim Launch machen",
            "body": "Sehr geehrter Herr Schröder,\n\nes gibt einen Fehler, den wir immer wieder bei Startups sehen: Sie fokussieren zu früh auf das Produkt – und zu spät auf die Systematisierung des Vertriebs.\n\nDas führt dazu, dass großartige Produkte nicht die Traktion bekommen, die sie verdienen.\n\nKI kann hier ein Game-Changer sein: nicht als Gimmick, sondern als echtes Werkzeug für skalierbare Kundengewinnung.\n\nFür BauTech Solutions könnte das bedeuten: Mehr qualifizierte Gespräche, weniger manuelle Arbeit, schnelleres Feedback aus dem Markt.\n\nIch würde gerne konkret werden. Darf ich Ihnen zeigen, was ich meine?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 4, "scheduled_day": 14,
            "subject": "Mein letzter Versuch",
            "body": "Sehr geehrter Herr Schröder,\n\ndie nächste Mail werde ich Ihnen nicht mehr schreiben – das verspreche ich.\n\nAber ich wäre kein guter Vertriebsmensch, wenn ich nicht noch einmal fragen würde:\n\nHat das Thema KI-gestützte Kundengewinnung bei BauTech Solutions gerade keine Priorität?\n\nWenn Sie antworten – selbst mit 'nein' – wäre ich Ihnen dankbar. So weiß ich, dass die Energie anderswo besser investiert ist.\n\nFalls doch Interesse besteht: Ein 20-minütiges Gespräch reicht, um zu sehen, ob wir zueinander passen.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
    ],
    "Retail Innovation KG": [
        {
            "touchpoint_num": 1, "scheduled_day": 1,
            "subject": "Kundenanalyse bei Retail Innovation – 20 Minuten?",
            "body": "Sehr geehrte Frau Zimmermann,\n\nim Retail ist Customer Analytics nicht mehr optional – es ist die Voraussetzung für relevante Kundenerlebnisse.\n\nIch habe Retail Innovation KG als ein Unternehmen wahrgenommen, das Innovation nicht nur im Namen trägt. Daher die direkte Frage: Wie zufrieden sind Sie mit Ihrer aktuellen Datenstrategie?\n\nKI Katapult hilft Retail-Unternehmen, ihre Kundendaten in echte Handlungsempfehlungen zu verwandeln – in Echtzeit, personalisiert und mit messbarem Impact auf Conversion und Kundenbindung.\n\nEin 20-minütiges Gespräch würde zeigen, ob das für Retail Innovation KG relevant ist.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 2, "scheduled_day": 3,
            "subject": "+23 % Conversion durch besseres Kundenverständnis",
            "body": "Sehr geehrte Frau Zimmermann,\n\nnur eine kurze Nachfrage – und ein Ergebnis, das ich teilen wollte:\n\nFashionHub, ein Omnichannel-Retailer, hat mit unserer KI-Analytics-Lösung:\n- Die Conversion Rate um 23 % gesteigert\n- Den durchschnittlichen Warenkorbwert um 17 % erhöht\n- Die Churn Rate bei Stammkunden um 31 % reduziert\n\nDas war möglich durch besseres Verständnis der Customer Journey und gezieltes Targeting zum richtigen Zeitpunkt.\n\nIch glaube, Retail Innovation KG hat ähnliches Potenzial. Haben Sie 20 Minuten?\n\nViele Grüße,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 3, "scheduled_day": 7,
            "subject": "Was Ihre Kundendaten Ihnen noch nicht gesagt haben",
            "body": "Sehr geehrte Frau Zimmermann,\n\ndie meisten Retail-Unternehmen haben mehr Kundendaten als sie denken – aber zu wenig Kapazität, sie auszuwerten.\n\nDas führt zu einem paradoxen Problem: Je mehr Daten, desto mehr Rauschen – und desto schwieriger, echte Insights zu gewinnen.\n\nKI Katapult macht aus diesem Rauschen Signal: Wir identifizieren die Muster, die wirklich wichtig sind, und übersetzen sie in konkrete Handlungen für Ihr Team.\n\nFür Retail Innovation KG könnte das ein echter Wettbewerbsvorteil sein – besonders wenn Sie bereits eine starke Kundenbasis haben.\n\nDarf ich Ihnen in einem kurzen Gespräch zeigen, was ich meine?\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
        {
            "touchpoint_num": 4, "scheduled_day": 14,
            "subject": "Letzte Nachricht – und ein Angebot",
            "body": "Sehr geehrte Frau Zimmermann,\n\ndies ist meine letzte Mail. Ich möchte Ihnen jedoch vor meinem Abgang noch etwas mitgeben:\n\nFür Unternehmen wie Retail Innovation KG bieten wir gelegentlich einen kostenlosen 'Data Opportunity Audit' an – eine 45-minütige Analyse, bei der wir zeigen, welche KI-Potenziale in Ihren Daten stecken.\n\nKeine Verpflichtung, kein Sales-Pitch – nur ein ehrlicher Blick auf das, was möglich ist.\n\nFalls Sie Interesse haben, antworten Sie einfach auf diese Mail.\n\nMit freundlichen Grüßen,\nMax Müller\nKI Katapult",
        },
    ],
}


def get_demo_data():
    return DEMO_CAMPAIGN, DEMO_LEADS, DEMO_SEQUENCES
