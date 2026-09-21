GOLD = [
    {
        "id": "otif-late",
        "question": "Why is OTIF low and which warehouses drive late deliveries?",
        "agent": "analytics",
        "must_include": ["otif", "warehouse"],
    },
    {
        "id": "forecast-rev",
        "question": "Why did revenue move from 2016 to 2017 and what does the demand forecast say?",
        "agent": "forecast",
        "must_include": ["2016", "2017"],
    },
    {
        "id": "inventory",
        "question": "Which products look like stockout risk and what is coverage?",
        "agent": "inventory",
        "must_include": ["stockout", "coverage"],
    },
    {
        "id": "risk-late",
        "question": "What is the late-line revenue pool and who owns the top exception?",
        "agent": "risk",
        "must_include": ["late"],
    },
    {
        "id": "rag-otif",
        "question": "What does SAMPLE OTIF policy say about escalation?",
        "agent": "rag",
        "must_include": ["sample", "otif"],
    },
    {
        "id": "decision",
        "question": "What action should we take next on the highest-$ late warehouse?",
        "agent": "decision",
        "must_include": ["late", "warehouse"],
    },
]
